"""СЕРВИС ПРОДОЛЖЕНИЯ ОБУЧЕНИЯ

Определяет следующий урок курса для текущего пользователя.

Правила проекта:
    * доступны только опубликованные модули и опубликованные уроки;
    * урок считается завершённым, если у пользователя есть хотя бы одна
      попытка с максимальной оценкой correctness;
    * порядок прохождения — module.position, затем lesson.position.

Последним завершённым считается урок с максимальной позицией в этом
порядке. Следующий урок — первый доступный незавершённый урок в порядке
курса. Если завершённых уроков нет, обучение начинается с первого
доступного урока. Если все доступные уроки завершены, следующего урока
нет.
"""

from fastapi import Request
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import (
    ContinueLearningResponse,
    CourseShortInfo,
    LearningLessonInfo,
)
from app.api.v1.services.courses import BaseCoursesService
from app.models.courses import CourseModule, Lesson
from app.models.enrollments_progress import COMPLETED_CORRECTNESS, LessonAttempt


class LearningService(BaseCoursesService):
    """ПРОГРЕСС ПОЛЬЗОВАТЕЛЯ И СЛЕДУЮЩИЙ УРОК"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_next_lesson(
            self,
            request: Request,
            course_slug: str,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> ContinueLearningResponse:
        """СЛЕДУЮЩИЙ УРОК КУРСА ДЛЯ ПОЛЬЗОВАТЕЛЯ"""

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

        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        # прогресс доступен только записанным на курс; админского
        # обхода здесь нет: следующий урок — персональное состояние
        if not is_enrolled:
            await self._raise(
                request=request,
                code="COURSE_NOT_ENROLLED",
                error=error,
            )

        # завершённость проверяется одним коррелированным EXISTS,
        # чтобы не делать запрос на каждый урок
        is_completed = exists(
            select(LessonAttempt.attempt_id)
            .where(
                LessonAttempt.user_id == user_id,
                LessonAttempt.lesson_id == Lesson.lesson_id,
                LessonAttempt.correctness == COMPLETED_CORRECTNESS,
            )
            .correlate(Lesson)
        )

        result = await self.db.execute(
            select(
                CourseModule.module_id.label("module_id"),
                CourseModule.title.label("module_title"),
                CourseModule.position.label("module_position"),
                Lesson.lesson_id.label("lesson_id"),
                Lesson.title.label("title"),
                Lesson.description.label("description"),
                Lesson.position.label("position"),
                is_completed.label("is_completed"),
            )
            .join(Lesson, Lesson.module_id == CourseModule.module_id)
            .where(
                CourseModule.course_id == course.course_id,
                CourseModule.is_published.is_(True),
                Lesson.is_published.is_(True),
            )
            .order_by(
                CourseModule.position,
                Lesson.position,
                Lesson.lesson_id,
            )
        )

        lessons = result.all()

        completed_indexes = [
            index
            for index, lesson in enumerate(lessons)
            if lesson.is_completed
        ]

        lessons_total = len(lessons)
        lessons_completed = len(completed_indexes)

        # последний завершённый — для отображения; он может оказаться
        # позже следующего урока, если в прогрессе есть пропуск
        last_completed = (
            lessons[completed_indexes[-1]]
            if completed_indexes
            else None
        )

        # продолжаем последовательно: предлагаем первый незавершённый
        # урок, а не урок после последнего завершённого по позиции
        next_lesson = next(
            (
                lesson
                for lesson in lessons
                if not lesson.is_completed
            ),
            None,
        )

        return ContinueLearningResponse(
            course=CourseShortInfo(
                course_id=course.course_id,
                slug=course.slug,
                title=course.title,
            ),
            last_completed_lesson=(
                self._to_lesson_info(last_completed)
                if last_completed is not None
                else None
            ),
            next_lesson=(
                self._to_lesson_info(next_lesson)
                if next_lesson is not None
                else None
            ),
            is_course_completed=(
                lessons_total > 0
                and lessons_completed == lessons_total
            ),
            lessons_total=lessons_total,
            lessons_completed=lessons_completed,
        )

    @staticmethod
    def _to_lesson_info(lesson) -> LearningLessonInfo:
        """УРОК ДЛЯ ОТВЕТА О ПРОДОЛЖЕНИИ ОБУЧЕНИЯ"""

        return LearningLessonInfo(
            module_id=lesson.module_id,
            module_title=lesson.module_title,
            module_position=lesson.module_position,
            lesson_id=lesson.lesson_id,
            title=lesson.title,
            description=lesson.description,
            position=lesson.position,
        )
