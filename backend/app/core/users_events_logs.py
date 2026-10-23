import logging
from datetime import datetime, timezone
from ipaddress import ip_address

from starlette.requests import HTTPConnection

from app.models.errors import UserEventLog
from app.core.clients_ip import get_client_ip, get_geoip
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# подставляется, если определить IP не удалось: колонка INET NOT NULL
UNKNOWN_IP = "0.0.0.0"


def _safe_ip(value: str | None) -> str:
    """IP, который гарантированно принимает колонка INET."""

    if value:
        try:
            return str(ip_address(value.strip()))

        except ValueError:
            pass

    return UNKNOWN_IP


async def user_event_logs(
        *,
        request: HTTPConnection,
        user_id: int | None = None,
        session_id: int | None = None,
        event: str,
        status_code: int | None = None,
        device_id: str | None = None,
        platform: str | None = None,
) -> None:
    """Пишет событие в users_event_logs.

    Логирование best-effort: сбой записи не должен менять ответ API
    и не должен подменять исходную ошибку.
    """

    now = datetime.now(timezone.utc)
    client_ip = None
    country_code = None
    is_proxy = None

    try:
        client_ip = get_client_ip(request)

        if client_ip:
            country_code, is_proxy = get_geoip(client_ip)

    except Exception:
        logger.exception("user_event_logs: failed to resolve client ip")

    request_method = getattr(request, "method", None)
    if request_method is None:
        request_method = "API"

    try:
        async with AsyncSessionLocal() as db:
            log = UserEventLog(
                user_id=user_id,
                session_id=session_id,
                event=event[:255],
                request_method=request_method[:16],
                request_path=request.url.path[:255],
                status_code=status_code,
                ip_address=_safe_ip(client_ip),
                country_code=country_code,
                is_proxy=is_proxy,
                device_id=device_id[:255] if device_id else None,
                platform=platform[:10] if platform else None,
                created_at=now,
            )

            db.add(log)
            await db.commit()

    except Exception:
        logger.exception(
            "user_event_logs failed: event=%s path=%s",
            event,
            getattr(request.url, "path", ""),
        )
