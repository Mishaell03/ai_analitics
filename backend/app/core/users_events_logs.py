from datetime import datetime, timezone
from sqlalchemy.orm import Session
from starlette.requests import HTTPConnection

from app.db.models import UserEventLogs
from app.utilit.client_ip import get_client_ip
from app.utilit.geoip import get_geoip


def user_event_logs(
        db: Session,
        *,
        request: HTTPConnection,
        user_id: int | None = None,
        session_id: int | None = None,
        event: str,
        status_code: int | None = None,
        device_id: str | None = None,
        platform: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    client_ip = get_client_ip(request)
    country_code = None
    is_proxy = None
    if client_ip:
        country_code, is_proxy = get_geoip(client_ip)

    request_method = getattr(request, "method", None)
    if request_method is None:
        request_method = "WEBSOCKET"

    log = UserEventLogs(
        user_id=user_id,
        session_id=session_id,
        event=event,
        request_method=request_method,
        request_path=request.url.path,
        status_code=status_code,
        ip_address=client_ip,
        country_code=country_code,
        is_proxy=is_proxy,
        device_id=device_id,
        platform=platform,
        created_at=now,
    )

    db.add(log)
    db.commit()