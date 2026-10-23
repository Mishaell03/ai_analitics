"""CSRF-проверка по Origin для state-changing запросов."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.csrf import CSRFOriginMiddleware, is_allowed_origin


def test_missing_origin_is_not_allowed():
    assert is_allowed_origin(None) is False
    assert is_allowed_origin("") is False


def test_same_origin_is_allowed():
    assert is_allowed_origin(
        "https://api.example.com",
        host="api.example.com",
        request_url="https://api.example.com/api/v1/change",
    ) is True


def test_same_origin_scheme_mismatch_is_rejected():
    # HTTP Origin к HTTPS-эндпоинту запрещён
    assert is_allowed_origin(
        "http://api.example.com",
        host="api.example.com",
        request_url="https://api.example.com/api/v1/change",
    ) is False


def test_configured_origin_is_allowed():
    assert is_allowed_origin(
        "https://app.example.com",
        host="api.example.com",
        allowed_origins=("https://app.example.com",),
    ) is True


def test_foreign_origin_is_blocked():
    assert is_allowed_origin(
        "https://evil.example",
        host="api.example.com",
    ) is False


def test_localhost_is_allowed_only_for_local_api():
    assert is_allowed_origin(
        "http://localhost:5173",
        host="127.0.0.1:8000",
    ) is True

    assert is_allowed_origin(
        "http://localhost:5173",
        host="api.example.com",
    ) is False


def test_null_origin_is_blocked():
    assert is_allowed_origin("null", host="api.example.com") is False


def make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CSRFOriginMiddleware)

    @app.post("/change")
    async def change():
        return {"ok": True}

    @app.get("/read")
    async def read():
        return {"ok": True}

    return app


client = TestClient(make_app())


def _client_with_session() -> TestClient:
    test_client = TestClient(make_app())
    test_client.cookies.set("session_token", "token")

    return test_client


def test_state_change_with_missing_origin_and_cookie_is_rejected():
    """Регрессионный тест: cookie-аутентифицированный POST без Origin/Referer блокируется."""
    response = _client_with_session().post("/change")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "CSRF_ORIGIN_MISSING"


def test_state_change_with_custom_header_is_allowed():
    """Не-браузерные клиенты могут использовать кастомный заголовок X-Requested-With."""
    response = _client_with_session().post(
        "/change",
        headers={"x-requested-with": "XMLHttpRequest"},
    )

    assert response.status_code == 200


def test_state_change_with_foreign_origin_is_rejected():
    response = _client_with_session().post(
        "/change",
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "CSRF_ORIGIN_NOT_ALLOWED"


def test_state_change_without_session_cookie_is_allowed():
    response = client.post(
        "/change",
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 200


def test_state_change_with_same_origin_is_allowed():
    response = _client_with_session().post(
        "/change",
        headers={"origin": "http://testserver"},
    )

    assert response.status_code == 200


def test_safe_method_is_not_checked():
    response = _client_with_session().get(
        "/read",
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 200


def test_referer_is_used_when_origin_is_missing():
    response = _client_with_session().post(
        "/change",
        headers={"referer": "https://evil.example/page"},
    )

    assert response.status_code == 403
