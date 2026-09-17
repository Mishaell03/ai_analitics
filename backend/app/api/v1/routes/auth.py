from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import BaseAuthResponse, BaseAuthRequest
from app.api.v1.services.auth import BaseAuthService
from app.core.database import get_db
from app.core.users_events_logs import user_event_logs

router = APIRouter()


@router.post("/register", response_model=BaseAuthResponse)
async def register_user(
        data: BaseAuthRequest,
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    session = await BaseAuthService(db).auth(
        data=data,
        request=request,
        is_register=True,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_USERS_REGISTRATION",
        status_code=200,
        device_id=session.device_id,
        user_id=session.user_id,
        session_id=session.session_id,
    )

    return (BaseAuthResponse(
        session=session.session,
    ))


@router.post("/auth", response_model=BaseAuthResponse)
async def auth_user(
        data: BaseAuthRequest,
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    session = await BaseAuthService(db).auth(
        data=data,
        request=request,
        is_register=False,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_USERS_AUTH",
        status_code=200,
        device_id=session.device_id,
        user_id=session.user_id,
        session_id=session.session_id,
    )

    return BaseAuthResponse(
        session=session.session,
    )
