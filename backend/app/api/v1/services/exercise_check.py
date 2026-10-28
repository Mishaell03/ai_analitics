"""ПРОВЕРКА ОТВЕТА УЧЕНИКА НА ОДНО ЗАДАНИЕ"""

import json
from collections.abc import Mapping

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.exercise_check import ExerciseCheckRequest
from app.api.v1.services.courses import BaseCoursesService
from app.models.enrollments_progress import (
    CourseEnrollment,
    LessonAttempt,
    PASSED_EXERCISE_CORRECTNESS,
    PASSED_EXERCISES_KEY,
)
from app.models.exercises import ExerciseAnswer


class ExerciseCheckService(BaseCoursesService):
    """ПРОВЕРЯЕТ ОТВЕТ, НЕ ВОЗВРАЩАЯ ЭТАЛОН УЧЕНИКУ."""

    async def check_answer(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            exercise_id: str,
            data: ExerciseCheckRequest,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> bool:
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )
        module = await self._get_module(
            request=request,
            course=course,
            module_id=module_id,
            error=error,
        )
        lesson = await self._get_lesson(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        enrollment_result = await self.db.execute(
            select(CourseEnrollment.enrollment_id).where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course.course_id,
            )
        )
        if enrollment_result.scalar_one_or_none() is None:
            await self._raise(
                request=request,
                code="COURSE_NOT_ENROLLED",
                error=error,
            )

        answer_result = await self.db.execute(
            select(ExerciseAnswer.answer).where(
                ExerciseAnswer.lesson_id == lesson.lesson_id,
                ExerciseAnswer.exercise_id == exercise_id,
            )
        )
        correct_answer = answer_result.scalar_one_or_none()
        if correct_answer is None:
            await self._raise(
                request=request,
                code="EXERCISE_ANSWER_NOT_FOUND",
                error=error,
            )

        expected = self._parse_answer(correct_answer)
        submitted = self._parse_answer(data.answer)
        if any(value is not None and value[0] == "code" for value in (expected, submitted)):
            raise HTTPException(422, detail={
                "code": "CODE_EXECUTION_REQUIRED",
                "message": "Use /api/v1/sandbox/execute for code exercises",
            })

        is_correct = self.answers_match(data.answer, correct_answer)

        if is_correct:
            # Сохраняем только успешно проверенный ответ. Он связан с
            # пользователем и уроком и будет показан при повторном запросе.
            self.db.add(
                LessonAttempt(
                    user_id=user_id,
                    lesson_id=lesson.lesson_id,
                    answers={PASSED_EXERCISES_KEY: {exercise_id: data.answer}},
                    correctness=PASSED_EXERCISE_CORRECTNESS,
                    speed=0,
                )
            )
            await self.db.commit()

        return is_correct

    @staticmethod
    def answers_match(submitted: str, expected: str) -> bool:
        """Сравнивает ответы в формате buildAnswer; legacy-ответы — как текст."""

        submitted_value = ExerciseCheckService._parse_answer(submitted)
        expected_value = ExerciseCheckService._parse_answer(expected)

        if submitted_value is None and expected_value is None:
            return submitted == expected

        if submitted_value is None:
            expected_type, expected_content = expected_value
            return (
                expected_type in {"text", "code"}
                and expected_content == submitted
            )

        if expected_value is None:
            submitted_type, submitted_content = submitted_value
            return (
                submitted_type in {"text", "code"}
                and submitted_content == expected
            )

        submitted_type, submitted_content = submitted_value
        expected_type, expected_content = expected_value
        if submitted_type != expected_type:
            return False

        if expected_type == "choice":
            if not isinstance(submitted_content, list) or not isinstance(expected_content, list):
                return False
            return sorted(submitted_content) == sorted(expected_content)

        return submitted_content == expected_content

    @staticmethod
    def _parse_answer(value: str) -> tuple[str, str | list[str]] | None:
        """Читает структурированный ответ frontend; незнакомый JSON не угадывает."""

        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None

        if not isinstance(parsed, Mapping):
            return None

        answer_type = parsed.get("type")
        if answer_type == "choice":
            content = parsed.get("correct")
            if isinstance(content, list) and all(isinstance(item, str) for item in content):
                return answer_type, content
            return None

        if answer_type in {"text", "code"}:
            content = parsed.get("value")
            if isinstance(content, str):
                return answer_type, content

        return None
