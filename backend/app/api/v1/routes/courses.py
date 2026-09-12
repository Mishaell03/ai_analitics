from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import CoursesResponse
from app.api.v1.services.courses import BaseCoursesService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user
from app.core.users_events_logs import user_event_logs


router = APIRouter()


@router.get(
    "/courses",
    response_model=CoursesResponse,
)
async def get_courses(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current: CurrentUserContext = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
):
    courses = await BaseCoursesService(db).get_courses(
        page=page,
        page_size=page_size,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_COURSES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform
    )

    return courses