import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection
from fastapi import HTTPException, Request
from app.models.errors import BackendError, BackendErrorLocalization
from app.core.users_events_logs import user_event_logs


async def build_backend_error(
    db: AsyncSession,
    request: HTTPConnection,
    *,
    code: str,
    language: str = "en",
    user_id: int | None = None,
    session_id: int | None = None,
    device_id: str | None = None,
    platform: str | None = None,
) -> tuple[int, dict]:
    result = await db.execute(
        select(BackendError)
        .where(BackendError.code == code)
    )

    backend_error = result.scalar_one_or_none()

    if backend_error is None:
        logging.error(f"UNKNOWN_ERROR: {backend_error}")
        await user_event_logs(
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

    result = await db.execute(
        select(BackendErrorLocalization).where(
            BackendErrorLocalization.code == code,
            BackendErrorLocalization.language == language,
        )
    )
    localization = result.scalar_one_or_none()

    if localization is None:
        result = await db.execute(
            select(BackendErrorLocalization).where(
                BackendErrorLocalization.code == code,
                BackendErrorLocalization.language == "en",
            )
        )

        localization = result.scalar_one_or_none()

    await user_event_logs(
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

async def raise_backend_error(
        db: AsyncSession,
        request: Request,
    *,
        code: str,
        language: str = "en",
        user_id: int | None = None,
        session_id: int | None = None,
        device_id: str | None = None,
        platform: str | None = None,
) -> None:
    status_code, detail = await build_backend_error(
        db=db,
        request=request,
        code=code,
        language=language.lower(),
        user_id=user_id,
        session_id=session_id,
        device_id=device_id,
        platform=platform,
    )

    raise HTTPException(
        status_code=status_code,
        detail=detail,
    )