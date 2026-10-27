"""Rate limit на аутентификацию и защита от обхода через IP-spoofing."""

import asyncio
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import rate_limit as module
from app.core.rate_limit import FixedWindowLimiter, _rate_limit_key


def make_request(host: str = "203.0.113.10", headers: dict | None = None):
    return SimpleNamespace(
        client=SimpleNamespace(host=host),
        headers=headers or {},
    )


def test_limiter_blocks_after_limit(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    limiter = FixedWindowLimiter(limit=2, window_seconds=60)

    assert limiter.allow("k") == (True, 0)
    assert limiter.allow("k") == (True, 0)

    allowed, retry_after = limiter.allow("k")

    assert allowed is False
    assert retry_after >= 1


def test_limiter_window_resets(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    limiter = FixedWindowLimiter(limit=1, window_seconds=60)

    assert limiter.allow("k")[0] is True
    assert limiter.allow("k")[0] is False

    now[0] += 61

    assert limiter.allow("k")[0] is True


def test_limiter_isolates_keys():
    limiter = FixedWindowLimiter(limit=1, window_seconds=60)

    assert limiter.allow("a")[0] is True
    assert limiter.allow("b")[0] is True
    assert limiter.allow("a")[0] is False


def test_limiter_prune_bounded_memory(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    limiter = FixedWindowLimiter(limit=5, window_seconds=60, max_keys=100)
    for i in range(250):
        limiter.allow(f"ip_{i}")

    now[0] += 65
    limiter.allow("new_ip")

    # Истёкшие ключи должны быть удалены
    assert len(limiter._hits) <= 100


def test_spoofed_x_forwarded_for_from_untrusted_peer_is_ignored():
    """Регрессионный тест: клиент не может обойти rate limit сменой X-Forwarded-For."""
    req1 = make_request(host="203.0.113.10", headers={"x-forwarded-for": "1.1.1.1"})
    req2 = make_request(host="203.0.113.10", headers={"x-forwarded-for": "2.2.2.2"})

    # Так как 203.0.113.10 не является доверенным прокси, заголовок X-Forwarded-For игнорируется
    key1 = _rate_limit_key(req1)
    key2 = _rate_limit_key(req2)

    assert key1 == "203.0.113.10"
    assert key2 == "203.0.113.10"
    assert key1 == key2  # Оба запроса попадают под один и тот же лимит!


def test_spoofed_leftmost_ip_behind_trusted_proxy_is_ignored():
    """Регрессионный тест: за доверенным прокси X-Forwarded-For читается справа налево."""
    # 127.0.0.1 — доверенный прокси
    # Атакующий подставляет 100.1.1.1, прокси дописывает реальный сокет 198.51.100.5
    req1 = make_request(host="127.0.0.1", headers={"x-forwarded-for": "100.1.1.1, 198.51.100.5"})
    req2 = make_request(host="127.0.0.1", headers={"x-forwarded-for": "200.2.2.2, 198.51.100.5"})

    key1 = _rate_limit_key(req1)
    key2 = _rate_limit_key(req2)

    # Определяется настоящий клиентский IP (198.51.100.5), а не левые подделки
    assert key1 == "198.51.100.5"
    assert key2 == "198.51.100.5"
    assert key1 == key2


def test_malformed_forwarded_header_does_not_crash_rate_limiting():
    req = make_request(host="127.0.0.1", headers={"x-forwarded-for": "malformed;injection, not-an-ip"})
    key = _rate_limit_key(req)

    # Безопасно откатывается на IP доверенного пира, не выбрасывая 500 исключение
    assert key == "127.0.0.1"


def test_login_dependency_raises_429(monkeypatch):
    module.reset_auth_rate_limits()
    monkeypatch.setattr(module.settings, "auth_rate_limit_enabled", True)

    try:
        for _ in range(module.login_limiter.limit):
            asyncio.run(module.login_rate_limit(make_request()))

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(module.login_rate_limit(make_request()))

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail["code"] == "TOO_MANY_REQUESTS"
        assert "Retry-After" in exc_info.value.headers

    finally:
        module.reset_auth_rate_limits()


def test_dependency_can_be_disabled(monkeypatch):
    module.reset_auth_rate_limits()
    monkeypatch.setattr(module.settings, "auth_rate_limit_enabled", False)

    try:
        for _ in range(module.login_limiter.limit + 5):
            asyncio.run(module.login_rate_limit(make_request()))

    finally:
        module.reset_auth_rate_limits()
