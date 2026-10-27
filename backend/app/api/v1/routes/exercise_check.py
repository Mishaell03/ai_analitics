"""API УЧЕНИКА ДЛЯ ПРОВЕРКИ ОТВЕТА НА ЗАДАНИЕ"""

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.exercise_check import ExerciseCheckRequest
from app.api.v1.schemas.exercises import EXERCISE_ID_PATTERN
from app.api.v1.services.exercise_check import ExerciseCheckService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/courses")

ExerciseId = Path(
    ...,
    min_length=1,
    max_length=64,
    pattern=EXERCISE_ID_PATTERN,
    description="Идентификатор задания из Markdown урока",
)


@router.post(
    "/{course_slug}/modules/{module_id}/lessons/{lesson_id}/exercises/{exercise_id}/check",
    response_model=bool,
)
async def check_exercise_answer(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        data: ExerciseCheckRequest,
        exercise_id: str = ExerciseId,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    result = await ExerciseCheckService(db).check_answer(
        request=request,
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        exercise_id=exercise_id,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CHECK_EXERCISE_ANSWER",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result
