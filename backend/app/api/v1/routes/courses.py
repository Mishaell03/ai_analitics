from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import CoursesResponse, CourseDetailResponse
from app.api.v1.services.courses import BaseCoursesService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user
from app.core.users_events_logs import user_event_logs
from app.core.errors import raise_backend_error

router = APIRouter()


@router.get("/courses", response_model=CoursesResponse)
async def get_courses(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
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

@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
async def get_course(
        course_id: int,
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    course = await BaseCoursesService(db).get_course(
        course_id=course_id,
        page=page,
        page_size=page_size,
    )

    if course is None:
        await raise_backend_error(
            db=db,
            request=request,
            code="COURSE_NOT_FOUND",
            language=current.session.language,
            device_id=current.session.device_id,
            session_id=current.session.id,
            user_id=current.user.user_id,
            platform=current.session.platform,
        )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course
