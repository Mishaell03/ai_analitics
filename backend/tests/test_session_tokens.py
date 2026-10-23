"""Хранение сессионных токенов, защита от утечки БД и logout."""

import asyncio
from datetime import datetime
from app.core.session import revoke_session
from app.core.tokens import hash_session_token, token_candidates


class FakeResult:
    def __init__(self, session):
        self._session = session

    def scalar_one_or_none(self):
        return self._session


class FakeDb:
    def __init__(self, session):
        self.session = session
        self.committed = False
        self.query = None

    async def execute(self, query):
        self.query = query
        return FakeResult(self.session)

    async def commit(self):
        self.committed = True


class FakeSession:
    revoked_at = None


def test_hash_is_stable_and_differs_from_token():
    token = "secret-token"

    first = hash_session_token(token)
    second = hash_session_token(f"  {token}  ")

    assert first == second
    assert first != token
    assert len(first) == 64
    int(first, 16)  # валидный hex


def test_candidates_strictly_hashes_token():
    token = "user-secret-token"
    candidates = token_candidates(token)

    # Кандидаты поиска должны содержать ТОЛЬКО хэш
    assert len(candidates) == 1
    assert candidates[0] == hash_session_token(token)
    # Сырой токен ни при каких обстоятельствах не должен быть кандидатом
    assert token not in candidates


def test_db_hash_cannot_authenticate_as_session_cookie():
    """Регрессионный тест: утекший дамп БД не позволяет авторизоваться.

    В БД лежит: hash_session_token(raw_secret)
    Атакующий отправляет этот хэш в cookie.
    Сервер хэширует полученное значение: hash(hash) != hash.
    """
    raw_secret = "super-secret-user-cookie-token"
    stored_db_hash = hash_session_token(raw_secret)

    # Легитимный пользователь: присылает raw_secret
    client_token_legit = raw_secret
    assert hash_session_token(client_token_legit) == stored_db_hash

    # Атакующий, укравший дамп БД: присылает stored_db_hash в cookie
    client_token_attacker = stored_db_hash
    computed_lookup_hash = hash_session_token(client_token_attacker)

    # Хэш от хэша никогда не равен исходному хэшу в БД
    assert computed_lookup_hash != stored_db_hash


def test_revoke_session_marks_it_revoked():
    session = FakeSession()
    db = FakeDb(session)

    revoked = asyncio.run(revoke_session(db, "some-token"))

    assert revoked is True
    assert isinstance(session.revoked_at, datetime)
    assert db.committed is True


def test_revoke_session_is_idempotent_when_missing():
    db = FakeDb(None)

    revoked = asyncio.run(revoke_session(db, "some-token"))

    assert revoked is False
    assert db.committed is False
