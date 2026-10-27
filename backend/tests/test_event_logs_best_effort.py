"""Логирование событий не должно ломать ответ API и безопасно работает с INET."""

import asyncio
from types import SimpleNamespace

from app.core import users_events_logs as module
from app.core.clients_ip import safe_inet_ip


class FakeRequest:
    method = "POST"
    client = SimpleNamespace(host="10.0.0.1")
    headers = {}
    url = SimpleNamespace(path="/api/v1/auth")


class FailingSession:
    async def __aenter__(self):
        raise RuntimeError("database is down")

    async def __aexit__(self, *args):
        return False


class FakeSession:
    def __init__(self, store):
        self.store = store

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def add(self, value):
        self.store.append(value)

    async def commit(self):
        pass


def test_db_error_does_not_propagate(monkeypatch):
    monkeypatch.setattr(module, "AsyncSessionLocal", FailingSession)
    monkeypatch.setattr(module, "get_geoip", lambda ip: ("US", False))

    # не должно бросить исключение
    asyncio.run(
        module.user_event_logs(
            request=FakeRequest(),
            event="SUCCESS_USERS_AUTH",
        )
    )


def test_invalid_ip_is_replaced_and_fields_are_truncated(monkeypatch):
    logs = []

    monkeypatch.setattr(
        module,
        "AsyncSessionLocal",
        lambda: FakeSession(logs),
    )
    monkeypatch.setattr(module, "get_client_ip", lambda request: "not-an-ip")
    monkeypatch.setattr(module, "get_geoip", lambda ip: ("US", False))

    asyncio.run(
        module.user_event_logs(
            request=FakeRequest(),
            event="E" * 500,
            device_id="D" * 500,
            platform="P" * 50,
        )
    )

    assert len(logs) == 1
    log = logs[0]

    assert log.ip_address == module.UNKNOWN_IP
    assert len(log.event) == 255
    assert len(log.device_id) == 255
    assert len(log.platform) == 10


def test_safe_ip_accepts_valid_addresses():
    assert module._safe_ip("8.8.8.8") == "8.8.8.8"
    assert module._safe_ip(" 2001:db8::1 ") == "2001:db8::1"
    assert module._safe_ip(None) == module.UNKNOWN_IP
    assert module._safe_ip("999.1.1.1") == module.UNKNOWN_IP


def test_safe_inet_ip_for_nullable_columns():
    """Тест safe_inet_ip для колонок users_consents.ip, users_sessions.ip, backend_error_logs.ip_address."""
    assert safe_inet_ip("192.168.1.1") == "192.168.1.1"
    assert safe_inet_ip(" 10.0.0.1 ") == "10.0.0.1"
    assert safe_inet_ip("not-an-ip") is None
    assert safe_inet_ip("999.999.999.999") is None
    assert safe_inet_ip(None) is None
    assert safe_inet_ip("", default=None) is None
