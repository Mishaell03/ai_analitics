"""API ПОДТВЕРЖДЕНИЯ ПРОХОЖДЕНИЯ УРОКА"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.services.lesson_completion import LessonCompletionService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/courses")


@router.post(
    "/{course_slug}/modules/{module_id}/lessons/{lesson_id}/complete",
    response_model=bool,
)
async def complete_lesson(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    completed = await LessonCompletionService(db).complete_lesson(
        request=request,
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_COMPLETE_LESSON" if completed else "INCOMPLETE_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return completed
