import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from starlette.requests import HTTPConnection

from app.core.clients_ip import get_client_ip, get_geoip, safe_inet_ip
from app.core.database import AsyncSessionLocal
from app.core.tokens import hash_session_token
from app.models.auth import UserSession
from app.models.errors import BackendErrorLog

# поля, которые никогда не попадают в backend_error_logs
SENSITIVE_BODY_KEYS = frozenset({
    "password",
    "new_password",
    "old_password",
    "password_hash",
    "password_confirm",
    "token",
    "access_token",
    "refresh_token",
    "session",
    "session_token",
    "cookie",
    "cookies",
    "authorization",
    "secret",
    "api_key",
    "solutions",
    "answer",
    "code",
    "question",
    "user_context",
})

SENSITIVE_VALUE = "***"

MAX_BODY_LENGTH = 4000
MAX_ERROR_MESSAGE_LENGTH = 2000


def _sanitize(value):
    """Рекурсивно вычищает секреты из тела запроса."""
    if isinstance(value, dict):
        return {
            key: SENSITIVE_VALUE if key.lower() in SENSITIVE_BODY_KEYS else _sanitize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_sanitize(item) for item in value]

    return value


def sanitize_request_body(body: bytes | str | None) -> str | None:
    if not body:
        return None

    raw = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body

    sanitized = None

    try:
        sanitized = json.dumps(_sanitize(json.loads(raw)), ensure_ascii=False)

    except (ValueError, TypeError):
        # тело не json - пробуем разобрать его как form-data
        sanitized = _sanitize_form_data(raw)

    return sanitized[:MAX_BODY_LENGTH]


def _sanitize_form_data(raw: str) -> str:
    if "=" not in raw:
        return raw

    pairs = []

    for pair in raw.split("&"):
        key, _, value = pair.partition("=")

        if key.lower() in SENSITIVE_BODY_KEYS:
            value = SENSITIVE_VALUE

        pairs.append(f"{key}={value}")

    return "&".join(pairs)


async def resolve_session_id(
        request: HTTPConnection,
) -> int | None:
    """Достаёт id сессии из куки session_token, если она есть."""
    session_token = getattr(request, "cookies", {}).get("session_token")

    if not session_token:
        return None

    now = datetime.now(timezone.utc)
    token_hash = hash_session_token(session_token)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserSession.id).where(
                UserSession.session == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )

        return result.scalar_one_or_none()


async def backend_error_logs(
        *,
        request: HTTPConnection,
        status_code: int,
        error_message: str | None = None,
        session_id: int | None = None,
        request_body: bytes | str | None = None,
) -> None:
    if session_id is None:
        try:
            session_id = await resolve_session_id(request)

        except Exception as e:
            logging.exception(f"resolve_session_id exception: {e}")
            session_id = None

    client_ip = None
    is_proxy = None

    try:
        client_ip = get_client_ip(request)

        if client_ip:
            _, is_proxy = get_geoip(client_ip)

    except Exception as e:
        logging.exception(f"get_client_ip exception: {e}")

    request_method = getattr(request, "method", None) or "API"

    async with AsyncSessionLocal() as db:
        try:
            log = BackendErrorLog(
                session_id=session_id,
                status_code=status_code,
                request_method=request_method,
                request_path=request.url.path[:255],
                request_body=sanitize_request_body(request_body),
                error_message=error_message[:MAX_ERROR_MESSAGE_LENGTH] if error_message else None,
                ip_address=safe_inet_ip(client_ip),
                is_proxy=is_proxy,
                created_at=datetime.now(timezone.utc),
            )

            db.add(log)
            await db.commit()

        except Exception as e:
            logging.exception(f"backend_error_logs exception: {e}")
            await db.rollback()
