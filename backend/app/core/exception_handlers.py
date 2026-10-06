import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.backend_error_logs import MAX_BODY_LENGTH, backend_error_logs

# тела запросов без явного content-length читать не нужно
CAPTURED_BODY_CONTENT_TYPES = ("application/json", "application/x-www-form-urlencoded", "multipart/form-data")

# статусы, которые попадают в backend_error_logs (все 5xx добавляются автоматически)
LOGGED_STATUS_CODES = frozenset({
    405,  # Method Not Allowed
    422,  # Unprocessable Entity
    429,  # Too Many Requests
})


class RequestBodyMiddleware(BaseHTTPMiddleware):
    """Кэширует тело запроса, чтобы exception handler мог его прочитать."""

    async def dispatch(self, request: Request, call_next):
        request.state.raw_body = None

        content_type = request.headers.get("content-type", "")

        if any(content_type.startswith(value) for value in CAPTURED_BODY_CONTENT_TYPES):
            try:
                raw_body = await request.body()

                if len(raw_body) <= MAX_BODY_LENGTH:
                    request.state.raw_body = raw_body

            except Exception as e:
                logging.exception(f"read request body exception: {e}")

        return await call_next(request)


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