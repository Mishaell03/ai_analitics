import logging
from sqlalchemy.orm import Session
from starlette.requests import HTTPConnection

from app.db.models import BackendErrors, BackendErrorsLocalization
from app.core.user_event_logs import user_event_logs


def build_backend_error(
    db: Session,
    request: HTTPConnection,
    *,
    code: str,
    language: str = "en",
    user_id: int | None = None,
    session_id: str | None = None,
    device_id: str | None = None,
    platform: str | None = None,
) -> tuple[int, dict]:
    backend_error = (
        db.query(BackendErrors)
        .filter(BackendErrors.code == code)
        .first()
    )

    if backend_error is None:
        logging.error(f"UNKNOWN_ERROR: {backend_error}")
        user_event_logs(
            db,
            request=request,
            event="UNKNOWN_ERROR",
            status_code=500,
            device_id=device_id,
            user_id=user_id,
            session_id=session_id,
            platform=platform,
        )

        return 500, {
            "code": "UNKNOWN_ERROR",
            "message": "Unknown backend error",
        }

    localization = (
        db.query(BackendErrorsLocalization)
        .filter(
            BackendErrorsLocalization.code == code,
            BackendErrorsLocalization.language == language,
        )
        .first()
    )

    if localization is None:
        localization = (
            db.query(BackendErrorsLocalization)
            .filter(
                BackendErrorsLocalization.code == code,
                BackendErrorsLocalization.language == "en",
            )
            .first()
        )

    user_event_logs(
        db,
        request=request,
        event=backend_error.code,
        status_code=backend_error.http_status,
        device_id=device_id,
        user_id=user_id,
        session_id=session_id,
        platform=platform,
    )

    return backend_error.http_status, {
        "code": backend_error.code,
        "message": localization.message if localization else backend_error.code,
    }
