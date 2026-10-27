"""ДОСТУП К ЗАДАНИЮ И ДОВЕРЕННЫЙ ВЫБОР РЕСУРСОВ"""

import json

from fastapi import HTTPException, Request
from sqlalchemy import select

from app.api.v1.schemas.sandbox import (
    ExecutionResult,
    ExerciseSubmissionResponse,
    SandboxExecuteRequest,
)
from app.api.v1.services.courses import BaseCoursesService
from app.api.v1.services.exercise_check import ExerciseCheckService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.rate_limit import FixedWindowLimiter
from app.core.session import CurrentUserContext
from app.models.enrollments_progress import (
    LessonAttempt,
    PASSED_EXERCISE_CORRECTNESS,
    PASSED_EXERCISES_KEY,
)
from app.models.exercises import ExerciseAnswer
from app.services.sandbox.config import SandboxSettings
from app.services.sandbox.transport import execute_code

execution_limiter = FixedWindowLimiter(limit=10, window_seconds=60)


class SandboxService(BaseCoursesService):
    async def execute(
            self,
            request: Request,
            data: SandboxExecuteRequest,
            current: CurrentUserContext,
    ) -> ExecutionResult:
        exercise = await StudentExerciseService(self.db).get_exercise(
            request=request, course_slug=data.course_slug, module_id=data.module_id,
            lesson_id=data.lesson_id, exercise_id=data.exercise_id, current=current,
        )
        if exercise.language is None or exercise.language != data.language:
            raise HTTPException(422, detail={
                "code": "EXERCISE_LANGUAGE_MISMATCH",
                "message": "Language does not match the exercise configuration",
            })
        if exercise.language == "sql":
            # Нет изолированного SQL runner. Прикладной engine не используется.
            raise HTTPException(503, detail={
                "code": "SQL_SANDBOX_UNAVAILABLE", "message": "SQL sandbox unavailable",
            })
        error = self._error(
            language=current.session.language, device_id=current.session.device_id,
            session_id=current.session.id, user_id=current.user.user_id,
            platform=current.session.platform,
        )
        result = await self.db.execute(select(ExerciseAnswer.answer_id).where(
            ExerciseAnswer.lesson_id == data.lesson_id,
            ExerciseAnswer.exercise_id == data.exercise_id,
        ))
        if result.scalar_one_or_none() is None:
            await self._raise(request=request, code="EXERCISE_ANSWER_NOT_FOUND", error=error)

        # Явный allowlist заданий. Не настроенное задание не запускается.
        profile = SandboxSettings().assignment_profiles.get(f"{data.lesson_id}:{data.exercise_id}")
        if profile is None:
            raise HTTPException(403, detail={"code": "SANDBOX_NOT_ENABLED", "message": "Sandbox is not enabled for this assignment"})
        allowed, retry_after = execution_limiter.allow(str(current.user.user_id))
        if not allowed:
            raise HTTPException(429, detail={
                "code": "TOO_MANY_REQUESTS", "message": "Too many executions, try again later",
            }, headers={"Retry-After": str(retry_after)})
        return await execute_code(code=data.code, profile=profile)

    async def submit(
            self,
            request: Request,
            data: SandboxExecuteRequest,
            current: CurrentUserContext,
    ) -> ExerciseSubmissionResponse:
        execution = await self.execute(request=request, data=data, current=current)
        succeeded = (
            execution.exit_code == 0 and not execution.timed_out
            and not execution.output_limited and not execution.memory_limited
        )
        # Используем существующую семантику проверки: точное сравнение кода,
        # а не stdout и не исполнение эталона вместе с недоверенным кодом.
        result = await self.db.execute(select(ExerciseAnswer.answer).where(
            ExerciseAnswer.lesson_id == data.lesson_id,
            ExerciseAnswer.exercise_id == data.exercise_id,
        ))
        expected = result.scalar_one_or_none()
        answer = json.dumps({"type": "code", "value": data.code}, ensure_ascii=False)
        is_correct = (
            ExerciseCheckService.answers_match(answer, expected)
            if succeeded and expected is not None else None
        )
        attempt = LessonAttempt(
            user_id=current.user.user_id, lesson_id=data.lesson_id, code=data.code,
            answers={PASSED_EXERCISES_KEY: {data.exercise_id: answer}} if is_correct else {},
            correctness=PASSED_EXERCISE_CORRECTNESS if is_correct else 0, speed=0,
        )
        self.db.add(attempt)
        await self.db.commit()
        return ExerciseSubmissionResponse(
            execution=execution, execution_succeeded=succeeded,
            is_correct=is_correct, attempt_id=attempt.attempt_id,
        )
