"""Задания ученика: опубликованный контент и персональный прогресс."""

from fastapi import HTTPException, Request

from app.api.v1.schemas.sandbox import StudentExerciseResponse
from app.api.v1.services.lesson_content import LessonContentService
from app.core.session import CurrentUserContext


class StudentExerciseService(LessonContentService):
    async def list_exercises(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            current: CurrentUserContext,
    ) -> list[StudentExerciseResponse]:
        content = await self.get_lesson_content(
            request=request, course_slug=course_slug, module_id=module_id,
            lesson_id=lesson_id, language=current.session.language,
            device_id=current.session.device_id, session_id=current.session.id,
            user_id=current.user.user_id, platform=current.session.platform,
        )
        exercises = []
        seen = set()
        for block in content.custom_blocks:
            if block.type not in {"test", "code"} or not isinstance(block.data, dict):
                continue
            exercise_id = block.data.get("exercise_id")
            if not exercise_id:
                continue
            if exercise_id in seen:
                raise HTTPException(409, detail={
                    "code": "EXERCISE_CONFIGURATION_INVALID",
                    "message": "Exercise identifiers must be unique",
                })
            seen.add(exercise_id)
            language = block.data.get("language")
            exercises.append(StudentExerciseResponse(
                exercise_id=exercise_id, body=block.data["body"], language=language,
                execution_enabled=language in {"python", "sql"},
                is_completed=exercise_id in content.completed_exercises,
            ))
        return exercises

    async def get_exercise(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            exercise_id: str,
            current: CurrentUserContext,
    ) -> StudentExerciseResponse:
        exercises = await self.list_exercises(
            request=request, course_slug=course_slug, module_id=module_id,
            lesson_id=lesson_id, current=current,
        )
        for exercise in exercises:
            if exercise.exercise_id == exercise_id:
                return exercise
        raise HTTPException(404, detail={
            "code": "EXERCISE_NOT_FOUND", "message": "Exercise not found",
        })
