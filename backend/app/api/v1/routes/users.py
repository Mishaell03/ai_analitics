from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import CurrentUserContext, get_current_user
from app.api.v1.schemas.users import MeResponse, MeUpdateRequest
from app.api.v1.services.users import UserService
from app.core.database import get_db
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/me")


@router.get("", response_model=MeResponse)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUserContext = Depends(get_current_user),
):
    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ME",
        status_code=200,
        device_id=current_user.session.device_id,
        user_id=current_user.session.user_id,
        session_id=current_user.session.id,
        platform=current_user.session.platform,
    )

    return await UserService(db).get_me(
        current_user=current_user,
    )


@router.patch("", response_model=MeResponse)
async def update_me(
    request: Request,
    data: MeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUserContext = Depends(get_current_user),
):
    result = await UserService(db).update_me(
        current_user=current_user,
        data=data,
        request=request,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_ME",
        status_code=200,
        device_id=current_user.session.device_id,
        user_id=current_user.session.user_id,
        session_id=current_user.session.id,
        platform=current_user.session.platform,
    )

    return result