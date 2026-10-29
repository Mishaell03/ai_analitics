"""ПОДТВЕРЖДЕНИЕ ПРОХОЖДЕНИЯ ТЕСТОВ И ОБЯЗАТЕЛЬНЫХ ЗАПУСКОВ УРОКА"""

from collections.abc import Collection
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.services.courses import BaseCoursesService
from app.api.v1.services.lesson_content import LessonContentService
from app.models.enrollments_progress import COMPLETED_CORRECTNESS, LessonAttempt


class LessonCompletionService(BaseCoursesService):
    """ЗАВЕРШАЕТ УРОК ПОСЛЕ ТЕСТОВ И ОБЯЗАТЕЛЬНЫХ ВЫПОЛНЕНИЙ КОДА."""

    async def complete_lesson(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> bool:
        lesson_content = await LessonContentService(self.db).get_lesson_content(
            request=request,
            course_slug=course_slug,
            module_id=module_id,
            lesson_id=lesson_id,
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        required_exercises = self.get_exercise_ids(lesson_content.custom_blocks)
        passed_exercises = lesson_content.completed_exercises
        reviewed = getattr(lesson_content, "expert_review_exercises", [])
        if not self.all_exercises_passed(required_exercises, set(passed_exercises) | set(reviewed)):
            return False

        already_completed = await self.db.execute(
            select(LessonAttempt.attempt_id)
            .where(
                LessonAttempt.user_id == user_id,
                LessonAttempt.lesson_id == lesson_id,
                LessonAttempt.correctness == COMPLETED_CORRECTNESS,
            )
            .limit(1)
        )
        if already_completed.scalar_one_or_none() is None:
            self.db.add(
                LessonAttempt(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    answers=passed_exercises,
                    correctness=COMPLETED_CORRECTNESS,
                    speed=0,
                )
            )
            await self.db.commit()

        return True

    @staticmethod
    def get_exercise_ids(custom_blocks) -> set[str]:
        """ИЗВЛЕКАЕТ ID ТЕСТОВ, КОТОРЫЕ МОЖНО ПРОВЕРИТЬ В УРОКЕ."""

        exercise_ids = set()
        for block in custom_blocks:
            if block.type not in {"test", "code"} or not isinstance(block.data, dict):
                continue
            if block.type == "code" and block.data.get("practice"):
                continue
            exercise_id = block.data.get("exercise_id")
            if isinstance(exercise_id, str) and exercise_id:
                exercise_ids.add(exercise_id)
        return exercise_ids

    @staticmethod
    def all_exercises_passed(required_exercises: set[str], passed_exercises: Collection[str]) -> bool:
        """ПРОВЕРЯЕТ, ЧТО КАЖДОЕ ЗАДАНИЕ УРОКА ЕСТЬ В ПРОГРЕССЕ УЧЕНИКА."""

        return required_exercises.issubset(passed_exercises)
