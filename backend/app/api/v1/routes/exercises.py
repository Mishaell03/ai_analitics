"""АДМИНСКИЙ API ПРАВИЛЬНЫХ ОТВЕТОВ НА ЗАДАНИЯ УРОКОВ

Отдельный роутер: ответы на задания — самостоятельный раздел,
который не связан с содержимым урока в MinIO.
"""

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import EnrollmentResponse
from app.api.v1.schemas.exercises import (
    EXERCISE_ID_PATTERN,
    ExerciseAnswerRequest,
    ExerciseAnswerResponse,
    ExerciseAnswersResponse,
)
from app.api.v1.services.exercise_answers import ExerciseAnswerService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_admin
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/admin/lessons")

# идентификатор задания: буквы, цифры, дефис и подчёркивание
ExerciseId = Path(
    ...,
    min_length=1,
    max_length=64,
    pattern=EXERCISE_ID_PATTERN,
    description="Идентификатор задания из Markdown урока",
)


@router.get(
    "/{lesson_id}/exercises",
    response_model=ExerciseAnswersResponse,
)
async def get_exercise_answers(
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    answers = await ExerciseAnswerService(db).list_answers(
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_EXERCISE_ANSWERS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return answers


@router.post(
    "/{lesson_id}/exercises/{exercise_id}/answer",
    response_model=ExerciseAnswerResponse,
)
async def set_exercise_answer(
        lesson_id: int,
        request: Request,
        data: ExerciseAnswerRequest,
        exercise_id: str = ExerciseId,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    answer = await ExerciseAnswerService(db).set_answer(
        lesson_id=lesson_id,
        exercise_id=exercise_id,
        data=data,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_SET_EXERCISE_ANSWER",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return answer


@router.delete(
    "/{lesson_id}/exercises/{exercise_id}/answer",
    response_model=EnrollmentResponse,
)
async def delete_exercise_answer(
        lesson_id: int,
        request: Request,
        exercise_id: str = ExerciseId,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await ExerciseAnswerService(db).delete_answer(
        lesson_id=lesson_id,
        exercise_id=exercise_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_EXERCISE_ANSWER",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result
