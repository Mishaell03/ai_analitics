from fastapi import APIRouter, Request, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import BaseAuthResponse, BaseAuthRequest
from app.api.v1.services.auth import BaseAuthService
from app.core.config import settings
from app.core.database import get_db
from app.core.users_events_logs import user_event_logs

router = APIRouter()


@router.post("/register", response_model=BaseAuthResponse)
async def register_user(
        data: BaseAuthRequest,
        request: Request,
        response: Response,
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

    response.set_cookie(
        key="session_token",
        value=session.session,
        httponly=True,
        secure=settings.is_product,
        samesite="lax",
        path="/",
        max_age=60*60*24*180,
    )

    return BaseAuthResponse(
        success=True,
    )


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
        success=True,
    )
