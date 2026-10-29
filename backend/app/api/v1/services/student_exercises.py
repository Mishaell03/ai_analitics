"""Задания ученика: опубликованный контент и персональный прогресс."""

from fastapi import HTTPException, Request
from sqlalchemy import select

from app.api.v1.schemas.sandbox import ExpertSolutionResponse, StudentExerciseResponse
from app.api.v1.services.lesson_content import LessonContentService
from app.api.v1.services.lesson_code_content import decode_solution
from app.core.session import CurrentUserContext
from app.models.exercises import ExerciseAnswer
from app.services.sandbox.chart_grading import is_chart_exercise


class StudentExerciseService(LessonContentService):
    async def get_expert_solution(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            exercise_id: str,
            current: CurrentUserContext,
    ) -> ExpertSolutionResponse:
        """Эталон — после проверки либо собственного запуска в режиме самопроверки."""

        exercise = await self.get_exercise(
            request=request, course_slug=course_slug, module_id=module_id,
            lesson_id=lesson_id, exercise_id=exercise_id, current=current,
        )
        if not exercise.execution_enabled:
            raise HTTPException(404, detail={"code": "EXPERT_SOLUTION_NOT_FOUND"})
        if exercise_id == "none" or exercise_id.startswith("practice_"):
            raise HTTPException(404, detail={"code": "EXPERT_SOLUTION_NOT_FOUND"})
        if is_chart_exercise(lesson_id, exercise_id) and not exercise.is_completed:
            raise HTTPException(403, detail={"code": "EXERCISE_NOT_COMPLETED"})
        if not exercise.is_completed and not exercise.expert_solution_available:
            raise HTTPException(403, detail={"code": "EXERCISE_NOT_COMPLETED"})
        raw = (await self.db.execute(select(ExerciseAnswer.answer).where(
            ExerciseAnswer.lesson_id == lesson_id,
            ExerciseAnswer.exercise_id == exercise_id,
        ))).scalar_one_or_none()
        solution = decode_solution(raw)
        if not exercise.is_completed and (not solution or solution.get("check_mode") != "self_review"):
            raise HTTPException(403, detail={"code": "EXERCISE_NOT_COMPLETED"})
        if (solution is None or solution.get("language") != exercise.language
                or not isinstance(solution.get("value"), str) or not solution["value"].strip()):
            raise HTTPException(404, detail={"code": "EXPERT_SOLUTION_NOT_FOUND"})
        return ExpertSolutionResponse(
            exercise_id=exercise_id, language=exercise.language, code=solution["value"],
        )

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
                expert_solution_available=language in {"python", "sql"} and (
                    exercise_id in content.completed_exercises
                    or (not is_chart_exercise(lesson_id, exercise_id)
                        and exercise_id in getattr(content, "expert_review_exercises", []))
                ),
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
