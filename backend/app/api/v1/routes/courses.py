from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import (
    CoursesResponse,
    CourseDetailResponse,
    LessonDetailResponse,
    LessonsResponse,
)
from app.api.v1.services.courses import BaseCoursesService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix='/courses')


@router.get("", response_model=CoursesResponse)
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


@router.get("/{course_id}", response_model=CourseDetailResponse)
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
        request=request,
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


@router.get("/{course_id}/modules/{module_id}", response_model=LessonsResponse )
async def get_lessons(
    course_id: int,
    module_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: CurrentUserContext = Depends(get_current_user),
):
    lessons = await BaseCoursesService(db).get_lessons(
        course_id=course_id,
        module_id=module_id,
        page=page,
        page_size=page_size,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_LESSONS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lessons


@router.get("/{course_id}/modules/{module_id}/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
        course_id: int,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    lesson = await BaseCoursesService(db).get_lesson(
        course_id=course_id,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lesson
