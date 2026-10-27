"""API заданий ученика и отправки кода на проверку."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.exercises import EXERCISE_ID_PATTERN
from app.api.v1.schemas.sandbox import (
    ExerciseSubmissionResponse,
    ExerciseSubmitRequest,
    SandboxExecuteRequest,
    StudentExerciseResponse,
)
from app.api.v1.services.sandbox import SandboxService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user

router = APIRouter(prefix="/courses")
ExerciseId = Annotated[str, Path(min_length=1, max_length=64, pattern=EXERCISE_ID_PATTERN)]
PositiveId = Annotated[int, Path(gt=0)]
CourseSlug = Annotated[str, Path(min_length=1, max_length=255)]
EXERCISES_PATH = "/{course_slug}/modules/{module_id}/lessons/{lesson_id}/exercises"


@router.get(EXERCISES_PATH, response_model=list[StudentExerciseResponse])
async def get_student_exercises(
        course_slug: CourseSlug,
        module_id: PositiveId,
        lesson_id: PositiveId,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    return await StudentExerciseService(db).list_exercises(
        request=request, course_slug=course_slug, module_id=module_id,
        lesson_id=lesson_id, current=current,
    )


@router.get(EXERCISES_PATH + "/{exercise_id}", response_model=StudentExerciseResponse)
async def get_student_exercise(
        course_slug: CourseSlug,
        module_id: PositiveId,
        lesson_id: PositiveId,
        exercise_id: ExerciseId,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    return await StudentExerciseService(db).get_exercise(
        request=request, course_slug=course_slug, module_id=module_id,
        lesson_id=lesson_id, exercise_id=exercise_id, current=current,
    )


@router.post(EXERCISES_PATH + "/{exercise_id}/submit", response_model=ExerciseSubmissionResponse)
async def submit_exercise(
        course_slug: CourseSlug,
        module_id: PositiveId,
        lesson_id: PositiveId,
        exercise_id: ExerciseId,
        request: Request,
        data: ExerciseSubmitRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    return await SandboxService(db).submit(
        request=request, current=current,
        data=SandboxExecuteRequest(
            course_slug=course_slug, module_id=module_id, lesson_id=lesson_id,
            exercise_id=exercise_id, **data.model_dump(),
        ),
    )
