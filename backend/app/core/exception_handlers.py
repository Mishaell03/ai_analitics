import json
import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.backend_error_logs import MAX_BODY_LENGTH, backend_error_logs
from app.core.config import settings
from app.services.sandbox.config import MAX_REQUEST_BYTES

# тела запросов, которые имеет смысл сохранять для диагностики.
# multipart/form-data намеренно не читается: это могут быть загрузки
# в сотни мегабайт, и буферизовать их в память нельзя.
CAPTURED_BODY_CONTENT_TYPES = ("application/json", "application/x-www-form-urlencoded")

# статусы, которые попадают в backend_error_logs (все 5xx добавляются автоматически)
LOGGED_STATUS_CODES = frozenset({
    405,  # Method Not Allowed
    422,  # Unprocessable Entity
    429,  # Too Many Requests
})


class RequestBodyMiddleware:
    """Чистый ASGI middleware для ограничения размера тела (HTTP 413)

    и кэширования небольших тел (до MAX_BODY_LENGTH) в request.state.raw_body
    для логов исключений без накладных расходов BaseHTTPMiddleware.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        state["raw_body"] = None

        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("latin-1").lower()

        # Для multipart/form-data допускаем большие загрузки видео
        path = scope.get("path", "").rstrip("/")
        is_execution = path == "/api/v1/sandbox/execute" or (
            path.startswith("/api/v1/courses/") and "/exercises/" in path and path.endswith("/submit")
        )
        if is_execution:
            max_allowed = MAX_REQUEST_BYTES
        elif content_type.startswith("multipart/form-data"):
            max_allowed = settings.media_max_video_size + (15 * 1024 * 1024)
        else:
            max_allowed = getattr(settings, "max_standard_body_size", 10 * 1024 * 1024)

        # 1. Быстрая проверка размера по заголовку Content-Length
        content_length_raw = headers.get(b"content-length")
        if content_length_raw:
            try:
                body_length = int(content_length_raw)
            except ValueError:
                body_length = 0

            if body_length > max_allowed:
                await self._send_413(send, max_allowed)
                return

        # 2. Потоковый подсчёт байт и селективное кэширование малых тел для логов
        bytes_received = 0
        buffered_chunks = []
        should_capture = not is_execution and any(
            content_type.startswith(val) for val in CAPTURED_BODY_CONTENT_TYPES
        )

        async def counting_receive():
            nonlocal bytes_received
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                bytes_received += len(chunk)
                if bytes_received > max_allowed:
                    raise ValueError("PAYLOAD_TOO_LARGE")

                if should_capture and bytes_received <= MAX_BODY_LENGTH:
                    buffered_chunks.append(chunk)
                    state["raw_body"] = b"".join(buffered_chunks)
                elif should_capture and bytes_received > MAX_BODY_LENGTH:
                    state["raw_body"] = None

            return message

        try:
            await self.app(scope, counting_receive, send)
        except ValueError as exc:
            if str(exc) == "PAYLOAD_TOO_LARGE":
                await self._send_413(send, max_allowed)
            else:
                raise

    @staticmethod
    async def _send_413(send, max_allowed: int):
        payload = json.dumps({
            "detail": {
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Request body exceeds maximum allowed size ({max_allowed} bytes)",
            }
        }).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode("utf-8")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": payload,
        })


async def _log_backend_error(
        request: Request,
        status_code: int,
        error_message: str,
) -> None:
    try:
        await backend_error_logs(
            request=request,
            status_code=status_code,
            error_message=error_message,
            request_body=getattr(request.state, "raw_body", None),
        )

    # логирование ошибки не должно ломать ответ клиенту
    except Exception as e:
        logging.exception(f"backend_error_logs exception: {e}")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.exception(f"unhandled exception: {exc}")

    await _log_backend_error(
        request=request,
        status_code=500,
        error_message=f"{type(exc).__name__}: {exc}",
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            }
        },
    )


def is_logged_status_code(status_code: int) -> bool:
    return status_code >= 500 or status_code in LOGGED_STATUS_CODES


async def server_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if is_logged_status_code(exc.status_code):
        logging.error(f"logged error: {exc.status_code} {exc.detail}")

        await _log_backend_error(
            request=request,
            status_code=exc.status_code,
            error_message=str(exc.detail),
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logging.error(f"logged error: 422 {exc.errors()}")

    await _log_backend_error(
        request=request,
        status_code=422,
        error_message=str(exc.errors()),
    )

    return await request_validation_exception_handler(request, exc)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_middleware(RequestBodyMiddleware)

    app.add_exception_handler(StarletteHTTPException, server_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
