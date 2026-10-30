"""Practice execution never loads or compares expert answers."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.v1.schemas.sandbox import ExecutionResult, SandboxExecuteRequest
from app.api.v1.services.sandbox import SandboxService


@pytest.mark.parametrize("exit_code", [0, 1])
@pytest.mark.parametrize("language", ["python", "sql"])
def test_practice_submission_is_ungraded_even_on_execution_error(exit_code, language):
    db = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    db.add = Mock(side_effect=lambda attempt: setattr(attempt, "attempt_id", 123))
    service = SandboxService(db)
    service.execute = AsyncMock(return_value=ExecutionResult(
        stdout="hello\n" if exit_code == 0 else "",
        stderr="test error" if exit_code else "",
        exit_code=exit_code, timed_out=False, duration=0.01,
    ))
    service.grade = Mock(side_effect=AssertionError("Practice must not be graded"))
    data = SandboxExecuteRequest(
        course_slug="ai-development-beginner", module_id=3, lesson_id=10,
        exercise_id=f"practice_{language}_42", language=language,
        code='print("hello")' if language == "python" else "SELECT 1;",
    )
    result = asyncio.run(service.submit(
        request=Mock(), data=data,
        current=SimpleNamespace(user=SimpleNamespace(user_id=1)),
    ))
    assert result.is_correct is None
    assert result.execution_succeeded == (exit_code == 0)
    db.execute.assert_not_awaited()
    service.grade.assert_not_called()
    attempt = db.add.call_args.args[0]
    assert attempt.answers["is_correct"] is None
    assert attempt.correctness == 0
