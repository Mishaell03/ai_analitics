"""RequestBodyMiddleware: ограничение размера (HTTP 413) и буферизация для логов."""

from fastapi import FastAPI, File, Request, UploadFile
from starlette.testclient import TestClient

from app.core.config import settings
from app.core.exception_handlers import MAX_BODY_LENGTH, RequestBodyMiddleware


def make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestBodyMiddleware)

    @app.post("/json")
    async def json_endpoint(request: Request):
        body = await request.body()

        return {
            "captured": request.state.raw_body is not None,
            "captured_len": len(request.state.raw_body or b""),
            "body_len": len(body),
        }

    @app.post("/upload")
    async def upload_endpoint(
            request: Request,
            file: UploadFile = File(...),
    ):
        content = await file.read()

        return {
            "captured": request.state.raw_body is not None,
            "file_len": len(content),
        }

    return app


client = TestClient(make_app())


def test_small_json_body_is_captured():
    response = client.post("/json", json={"login": "user"})

    assert response.status_code == 200
    assert response.json()["captured"] is True
    assert response.json()["captured_len"] <= MAX_BODY_LENGTH


def test_large_json_body_is_not_captured_but_still_delivered():
    payload = b'{"data":"' + b"x" * (MAX_BODY_LENGTH * 2) + b'"}'

    response = client.post(
        "/json",
        content=payload,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["captured"] is False
    # тело доходит до эндпоинта целиком, так как не превышает глобальный лимит 10 МБ
    assert response.json()["body_len"] == len(payload)


def test_oversized_body_returns_413(monkeypatch):
    """Регрессионный тест: запрос с телом больше разрешённого лимита отклоняется с кодом 413."""
    # Устанавливаем тестовый лимит 1000 байт
    monkeypatch.setattr(settings, "max_standard_body_size", 1000)

    oversized_payload = b"x" * 2000
    response = client.post(
        "/json",
        content=oversized_payload,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"


def test_chunked_stream_exceeding_limit_returns_413(monkeypatch):
    """Потоковая передача без Content-Length прерывается при превышении байт-лимита."""
    monkeypatch.setattr(settings, "max_standard_body_size", 500)

    def generator():
        for _ in range(10):
            yield b"x" * 100

    response = client.post(
        "/json",
        content=generator(),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"


def test_multipart_is_not_captured_and_file_is_intact():
    payload = b"x" * 64_000

    response = client.post(
        "/upload",
        files={"file": ("video.mp4", payload, "video/mp4")},
    )

    assert response.status_code == 200
    assert response.json()["captured"] is False
    assert response.json()["file_len"] == len(payload)
