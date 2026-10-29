"""ДОСТУП К ЗАДАНИЮ И ДОВЕРЕННЫЙ ВЫБОР РЕСУРСОВ"""

import json
from collections import Counter

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select

from app.api.v1.schemas.sandbox import (
    ExecutionResult,
    ExerciseSubmissionResponse,
    SandboxExecuteRequest,
)
from app.api.v1.services.courses import BaseCoursesService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.api.v1.services.lesson_code_content import decode_solution
from app.core.rate_limit import FixedWindowLimiter
from app.core.session import CurrentUserContext
from app.models.enrollments_progress import (
    LessonAttempt,
    PASSED_EXERCISE_CORRECTNESS,
    PASSED_EXERCISES_KEY,
)
from app.services.sandbox.config import SandboxSettings
from app.services.sandbox.transport import execute_code
from app.models.exercises import ExerciseAnswer

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
        profile = SandboxSettings().assignment_profiles.get(f"{data.lesson_id}:{data.exercise_id}", "light")
        allowed, retry_after = execution_limiter.allow(str(current.user.user_id))
        if not allowed:
            raise HTTPException(429, detail={
                "code": "TOO_MANY_REQUESTS", "message": "Too many executions, try again later",
            }, headers={"Retry-After": str(retry_after)})
        return await execute_code(code=data.code, profile=profile, language=data.language)

    async def submit(
            self,
            request: Request,
            data: SandboxExecuteRequest,
            current: CurrentUserContext,
    ) -> ExerciseSubmissionResponse:
        execution = await self.execute(request=request, data=data, current=current)
        succeeded = execution.success
        # The Markdown parser assigns practice_* IDs to id: none fields.
        # They never load an expert reference or contribute to passed exercises,
        # including when execution fails (the error is in execution.stderr).
        if data.exercise_id == "none" or data.exercise_id.startswith("practice_"):
            is_correct = None
        else:
            expected = (await self.db.execute(select(ExerciseAnswer.answer).where(
                ExerciseAnswer.lesson_id == data.lesson_id,
                ExerciseAnswer.exercise_id == data.exercise_id,
            ))).scalar_one_or_none()
            is_correct = self.grade(execution, expected, data.language)
        answer = json.dumps({"type": "code", "value": data.code}, ensure_ascii=False)
        attempt = LessonAttempt(
            user_id=current.user.user_id, lesson_id=data.lesson_id, code=data.code,
            answers={
                "execution": execution.model_dump(),
                "is_correct": is_correct,
                **({PASSED_EXERCISES_KEY: {data.exercise_id: answer}} if is_correct else {}),
            },
            correctness=PASSED_EXERCISE_CORRECTNESS if is_correct else 0, speed=0,
        )
        self.db.add(attempt)
        await self.db.commit()
        return ExerciseSubmissionResponse(
            execution=execution, execution_succeeded=succeeded,
            is_correct=is_correct, attempt_id=attempt.attempt_id,
        )

    @staticmethod
    def grade(execution: ExecutionResult, expected: str | None, language: str) -> bool | None:
        if not execution.success:
            return False
        solution = decode_solution(expected)
        if solution is None or solution.get("language") != language:
            return None
        try:
            reference = ExecutionResult.model_validate(solution.get("execution"))
        except ValidationError:
            return None
        if not reference.success:
            return None
        if language == "sql":
            try:
                actual = json.loads(execution.stdout)
                target = json.loads(reference.stdout)
            except (TypeError, ValueError):
                return None
            if not all(isinstance(value, dict) and isinstance(value.get("columns"), list)
                       and isinstance(value.get("rows"), list) for value in (actual, target)):
                return None
            if actual["columns"] != target["columns"]:
                return False
            if solution.get("ordered") is False:
                return Counter(json.dumps(row, sort_keys=True) for row in actual["rows"]) == Counter(
                    json.dumps(row, sort_keys=True) for row in target["rows"]
                )
            return actual["rows"] == target["rows"]
        # Разница CRLF/LF и завершающий перевод строки не меняют ответ.
        return (execution.stdout.replace("\r\n", "\n").rstrip("\n")
                == reference.stdout.replace("\r\n", "\n").rstrip("\n"))
