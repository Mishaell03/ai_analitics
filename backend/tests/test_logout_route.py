"""Контракт logout-эндпоинта (без обращения к БД)."""

from starlette.testclient import TestClient

from app.api.v1.routes import auth as auth_routes
from app.main import app

client = TestClient(app)


def test_logout_without_cookie_clears_cookie():
    response = client.post("/api/v1/logout")

    assert response.status_code == 200
    assert response.json() == {"success": True}

    set_cookie = response.headers.get("set-cookie", "")

    assert "session_token=" in set_cookie
    assert "Max-Age=0" in set_cookie


def test_logout_revokes_existing_session_and_records_event(monkeypatch):
    revoke_calls = []
    event_calls = []

    async def fake_revoke(db, session_token):
        revoke_calls.append(session_token)
        return True

    async def fake_event_log(*args, **kwargs):
        event_calls.append(kwargs.get("event"))

    monkeypatch.setattr(auth_routes, "revoke_session", fake_revoke)
    monkeypatch.setattr(auth_routes, "user_event_logs", fake_event_log)

    session_client = TestClient(app)
    session_client.cookies.set("session_token", "cookie-token")

    # Браузер отправляет Same-Origin или разрешённый Origin
    response = session_client.post(
        "/api/v1/logout",
        headers={"origin": "http://testserver"},
    )

    assert response.status_code == 200
    assert revoke_calls == ["cookie-token"]
    assert "SUCCESS_USERS_LOGOUT" in event_calls
