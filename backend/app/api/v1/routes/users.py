from fastapi import APIRouter, Depends, Request

from app.core.session import CurrentUserContext, get_current_user
from app.api.v1.schemas.users import MeResponse
from app.api.v1.services.users import user_service
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/me")


@router.get("", response_model=MeResponse )
async def get_me(
    request: Request,
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

    return await user_service.get_me(
        current_user=current_user,
    )