"""СЕРВИС ПРАВИЛЬНЫХ ОТВЕТОВ НА ЗАДАНИЯ УРОКОВ

Задания (тесты) хранятся в Markdown урока, правильные ответы — в БД.
Связь идёт через exercise_id: он указан в Markdown задания и повторяется
в ключе записи, поэтому ответ переживает правку текста задания.

Урок может не содержать заданий — тогда ответов у него просто нет.
"""

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.api.v1.schemas.exercises import (
    ExerciseAnswerRequest,
    ExerciseAnswerResponse,
    ExerciseAnswersResponse,
)
from app.api.v1.schemas.courses import EnrollmentResponse
from app.api.v1.services.courses import BaseCoursesService
from app.models.courses import Lesson
from app.models.exercises import ExerciseAnswer


class ExerciseAnswerService(BaseCoursesService):
    """УПРАВЛЕНИЕ ПРАВИЛЬНЫМИ ОТВЕТАМИ НА ЗАДАНИЯ"""

    async def set_answer(
            self,
            request: Request,
            lesson_id: int,
            exercise_id: str,
            data: ExerciseAnswerRequest,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> ExerciseAnswerResponse:
        """СОЗДАЁТ ИЛИ ОБНОВЛЯЕТ ПРАВИЛЬНЫЙ ОТВЕТ

        Один и тот же эндпоинт делает и то, и другое: если ответа
        ещё нет — он создаётся, если есть — обновляется.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        lesson = await self._get_lesson_by_id(
            request=request,
            lesson_id=lesson_id,
            error=error,
        )

        statement = insert(ExerciseAnswer).values(
            lesson_id=lesson.lesson_id,
            exercise_id=exercise_id,
            answer=data.answer,
        )

        statement = statement.on_conflict_do_update(
            index_elements=[
                ExerciseAnswer.lesson_id,
                ExerciseAnswer.exercise_id,
            ],
            set_={
                "answer": statement.excluded.answer,
                "updated_at": func.now(),
            },
        ).returning(ExerciseAnswer)

        result = await self.db.execute(statement)

        answer = result.scalar_one()

        await self.db.commit()

        return self._to_response(answer=answer)

    async def delete_answer(
            self,
            request: Request,
            lesson_id: int,
            exercise_id: str,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> EnrollmentResponse:
        """УДАЛЯЕТ ПРАВИЛЬНЫЙ ОТВЕТ ЗАДАНИЯ"""

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        lesson = await self._get_lesson_by_id(
            request=request,
            lesson_id=lesson_id,
            error=error,
        )

        result = await self.db.execute(
            select(ExerciseAnswer).where(
                ExerciseAnswer.lesson_id == lesson.lesson_id,
                ExerciseAnswer.exercise_id == exercise_id,
            )
        )

        answer = result.scalar_one_or_none()

        if answer is None:
            await self._raise(
                request=request,
                code="EXERCISE_ANSWER_NOT_FOUND",
                error=error,
            )

        await self.db.delete(answer)
        await self.db.commit()

        return EnrollmentResponse(success=True)

    async def list_answers(
            self,
            request: Request,
            lesson_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> ExerciseAnswersResponse:
        """ПРАВИЛЬНЫЕ ОТВЕТЫ УРОКА"""

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        lesson = await self._get_lesson_by_id(
            request=request,
            lesson_id=lesson_id,
            error=error,
        )

        result = await self.db.execute(
            select(ExerciseAnswer)
            .where(ExerciseAnswer.lesson_id == lesson.lesson_id)
            .order_by(ExerciseAnswer.exercise_id)
        )

        answers = result.scalars().all()

        return ExerciseAnswersResponse(
            lesson_id=lesson.lesson_id,
            answers=[self._to_response(answer=answer) for answer in answers],
        )

    # ---------- служебное ----------

    async def _get_lesson_by_id(
            self,
            request: Request,
            lesson_id: int | str,
            error: dict,
    ):
        """УРОК ПО ИДЕНТИФИКАТОРУ

        Урок ищется в любом модуле: админ работает с ответами
        конкретного задания, а не с деревом курса.
        """

        if not str(lesson_id).isdigit():
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        result = await self.db.execute(
            select(Lesson).where(Lesson.lesson_id == int(lesson_id))
        )

        lesson = result.scalar_one_or_none()

        if lesson is None:
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        return lesson

    @staticmethod
    def _to_response(answer: ExerciseAnswer) -> ExerciseAnswerResponse:
        """ОТВЕТ API С ПРАВИЛЬНЫМ ОТВЕТОМ"""

        return ExerciseAnswerResponse(
            answer_id=answer.answer_id,
            lesson_id=answer.lesson_id,
            exercise_id=answer.exercise_id,
            answer=answer.answer,
            created_at=answer.created_at,
            updated_at=answer.updated_at,
        )
