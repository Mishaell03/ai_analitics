"""ДОСТУП К ЗАДАНИЮ И ДОВЕРЕННЫЙ ВЫБОР РЕСУРСОВ"""

from fastapi import HTTPException, Request
from sqlalchemy import select

from app.api.v1.schemas.sandbox import ExecutionResult, SandboxExecuteRequest
from app.api.v1.services.courses import BaseCoursesService
from app.core.session import CurrentUserContext
from app.models.exercises import ExerciseAnswer
from app.services.sandbox.config import SandboxSettings
from app.services.sandbox.transport import execute_code


class SandboxService(BaseCoursesService):
    async def execute(
            self,
            request: Request,
            data: SandboxExecuteRequest,
            current: CurrentUserContext,
    ) -> ExecutionResult:
        error = self._error(
            language=current.session.language, device_id=current.session.device_id,
            session_id=current.session.id, user_id=current.user.user_id,
            platform=current.session.platform,
        )
        course = await self._get_course(request=request, course_slug=data.course_slug, error=error)
        module = await self._get_module(request=request, course=course, module_id=data.module_id, error=error)
        lesson = await self._get_lesson(request=request, module=module, lesson_id=data.lesson_id, error=error)
        if not await self._is_enrolled(user_id=current.user.user_id, course_id=course.course_id):
            await self._raise(request=request, code="COURSE_NOT_ENROLLED", error=error)

        result = await self.db.execute(select(ExerciseAnswer.answer_id).where(
            ExerciseAnswer.lesson_id == lesson.lesson_id,
            ExerciseAnswer.exercise_id == data.exercise_id,
        ))
        if result.scalar_one_or_none() is None:
            await self._raise(request=request, code="EXERCISE_ANSWER_NOT_FOUND", error=error)

        # Явный allowlist заданий. Не настроенное задание не запускается.
        profile = SandboxSettings().assignment_profiles.get(f"{lesson.lesson_id}:{data.exercise_id}")
        if profile is None:
            raise HTTPException(403, detail={"code": "SANDBOX_NOT_ENABLED", "message": "Sandbox is not enabled for this assignment"})
        return await execute_code(code=data.code, profile=profile)
