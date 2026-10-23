"""ЗАЩИТА ОТ CSRF ПО ORIGIN

Cookie сессии отправляется браузером автоматически, поэтому
state-changing запросы (POST, PUT, DELETE, PATCH), использующие
cookie-аутентификацию, проверяются на соответствие доверенным Origin/Referer.

Если запрос аутентифицирован через cookie, но заголовки Origin и Referer
отсутствуют (подавлены политикой rel=noreferrer или расширениями приватности),
запрос отклоняется (403 CSRF_ORIGIN_MISSING).

Для не-браузерных API-клиентов доступно использование заголовка X-Requested-With.
Запросы без сессионных cookie (публичные эндпоинты, Bearer-аутентификация)
пропускаются без CSRF-ограничений.
"""

import re
from urllib.parse import urlsplit

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# dev-фронтенд на любом свободном порту Vite
LOCALHOST_ORIGIN_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")

# API на localhost: только в этом случае разрешаем localhost-Origin
LOCALHOST_HOST_RE = re.compile(r"^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$", re.IGNORECASE)


def origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None

    parsed = urlsplit(referer)

    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}"


def _normalize_netloc(scheme: str, netloc: str) -> str:
    """Приводит netloc к каноническому виду без избыточных дефолтных портов (80/443)."""
    host_part, _, port_part = netloc.partition(":")
    host_part = host_part.lower()

    if not port_part:
        return host_part

    if (scheme == "http" and port_part == "80") or (scheme == "https" and port_part == "443"):
        return host_part

    return f"{host_part}:{port_part}"


def is_allowed_origin(
        origin: str | None,
        *,
        request_url: str | None = None,
        host: str | None = None,
        allowed_origins: tuple[str, ...] = (),
) -> bool:
    """Проверяет допустимость Origin для state-changing запроса."""
    if not origin:
        return False

    parsed_origin = urlsplit(origin)

    if not parsed_origin.scheme or not parsed_origin.netloc:
        return False

    origin_scheme = parsed_origin.scheme.lower()
    normalized_origin = f"{origin_scheme}://{parsed_origin.netloc}".rstrip("/").lower()

    # 1. Проверка по явному белому списку разрешённых доменов (CORS_ORIGINS)
    normalized_allowed = {item.rstrip("/").lower() for item in allowed_origins if item.strip()}
    if normalized_origin in normalized_allowed:
        return True

    # 2. Локальная разработка: localhost-фронтенд к localhost-API
    if (
        host
        and LOCALHOST_HOST_RE.match(host)
        and LOCALHOST_ORIGIN_RE.match(normalized_origin)
    ):
        return True

    # 3. Same-origin проверка (только при полном совпадении схемы, хоста и эффективного порта)
    target_scheme = None
    target_netloc = None

    if request_url:
        parsed_target = urlsplit(request_url)
        target_scheme = parsed_target.scheme.lower() if parsed_target.scheme else None
        target_netloc = parsed_target.netloc.lower() if parsed_target.netloc else None

    if not target_scheme:
        target_scheme = "https" if settings.is_product else origin_scheme

    if not target_netloc and host:
        target_netloc = host.lower()

    # Схема должна строго совпадать: HTTP-Origin к HTTPS-эндпоинту запрещён
    if target_scheme and origin_scheme != target_scheme:
        return False

    if target_netloc:
        norm_origin_netloc = _normalize_netloc(origin_scheme, parsed_origin.netloc)
        norm_target_netloc = _normalize_netloc(target_scheme, target_netloc)
        if norm_origin_netloc == norm_target_netloc:
            return True

    return False


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
                request.method not in SAFE_METHODS
                and request.cookies.get("session_token")
        ):
            # Не-браузерные клиенты могут использовать кастомный заголовок
            # Браузер не может отправить кастомный заголовок кросс-доменно без CORS preflight
            if request.headers.get("x-requested-with"):
                return await call_next(request)

            origin = request.headers.get("origin") or origin_from_referer(
                request.headers.get("referer")
            )

            if not origin:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "code": "CSRF_ORIGIN_MISSING",
                            "message": "Origin or Referer header is required for cookie-authenticated requests",
                        }
                    },
                )

            if not is_allowed_origin(
                    origin,
                    request_url=str(request.url),
                    host=request.headers.get("host"),
                    allowed_origins=settings.cors_origins,
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "code": "CSRF_ORIGIN_NOT_ALLOWED",
                            "message": "Request origin is not allowed",
                        }
                    },
                )

        return await call_next(request)
