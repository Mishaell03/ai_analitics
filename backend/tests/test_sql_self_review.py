"""Самопроверка SQL не сравнивает ответ с эталоном и не выставляет оценку."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.exercises import CodeSolution, LessonCodeContentRequest
from app.api.v1.schemas.sandbox import ExecutionResult, SandboxExecuteRequest
from app.api.v1.services import lesson_code_content as content_module
from app.api.v1.services.lesson_code_content import LessonCodeContentService
from app.api.v1.services.lesson_content import LessonContentService
from app.api.v1.services.sandbox import SandboxService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.markdown import MarkdownParser
from app.models.enrollments_progress import EXPERT_REVIEW_EXERCISES_KEY, PASSED_EXERCISES_KEY

MANIFEST = json.loads((Path(__file__).resolve().parents[1] / "docs/lesson-12/solutions.json").read_text())


def current():
    return SimpleNamespace(user=SimpleNamespace(user_id=7), session=SimpleNamespace(
        language="en", device_id="d", id=1, platform="web",
    ))


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("succeeded", [True, False])
def test_each_reference_is_unlocked_by_its_own_execution_without_grading(monkeypatch, index, succeeded):
    item = MANIFEST["assignments"][index]
    exercise_id = f"fixture_sql_{index + 1}"  # фикстура, не публикационные ID
    raw = json.dumps({"type": "code", "language": "sql", "check_mode": "self_review", "value": item["code"]})
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: raw)),
                         add=Mock(), commit=AsyncMock())

    async def commit():
        db.add.call_args.args[0].attempt_id = 1

    db.commit.side_effect = commit
    service = SandboxService(db)
    service.execute = AsyncMock(return_value=ExecutionResult(
        stdout='{"columns":["different"],"rows":[[1]]}' if succeeded else "",
        stderr="" if succeeded else "SQL error", exit_code=0 if succeeded else 1,
        timed_out=False, duration=0.1,
    ))
    grade = Mock(side_effect=AssertionError("Самопроверка не вызывает grade"))
    monkeypatch.setattr(service, "grade", grade)
    result = asyncio.run(service.submit(object(), SandboxExecuteRequest(
        course_slug="demo", module_id=4, lesson_id=100, exercise_id=exercise_id,
        language="sql", code="SELECT * FROM retail_order_items LIMIT 1",
    ), current()))
    assert result.is_correct is None
    assert result.check_mode == "self_review"
    assert result.expert_solution_available is succeeded
    grade.assert_not_called()
    attempt = db.add.call_args.args[0]
    assert PASSED_EXERCISES_KEY not in attempt.answers
    assert attempt.correctness == 0
    reviews = LessonContentService._merge_expert_reviews([attempt])
    assert reviews == ([exercise_id] if succeeded else [])
    assert LessonContentService._merge_completed_exercises([attempt]) == {}

    content = SimpleNamespace(custom_blocks=MarkdownParser().parse(
        f":::code sql\nid: {exercise_id}\n:::\n:::code sql\nid: unrelated\n:::"
    ).custom_blocks, completed_exercises={}, expert_review_exercises=reviews)
    student = StudentExerciseService(db)
    student.get_lesson_content = AsyncMock(return_value=content)
    if succeeded:
        solution = asyncio.run(student.get_expert_solution(object(), "demo", 4, 100, exercise_id, current()))
        assert solution.code == item["code"]
        assert student.get_lesson_content.call_args.kwargs["user_id"] == 7
    else:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(student.get_expert_solution(object(), "demo", 4, 100, exercise_id, current()))
        assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc:
        asyncio.run(student.get_expert_solution(object(), "demo", 4, 100, "unrelated", current()))
    assert exc.value.status_code == 403


@pytest.mark.parametrize("execution", [None, {}, {"exit_code": 1}, {
    "stdout": "", "stderr": "", "exit_code": 0, "timed_out": True, "duration": 1,
}])
def test_invalid_or_failed_execution_does_not_open_expert_code(execution):
    attempt = SimpleNamespace(answers={EXPERT_REVIEW_EXERCISES_KEY: ["fixture"], "execution": execution})
    assert LessonContentService._merge_expert_reviews([attempt]) == []


def test_reference_can_be_saved_without_running_or_comparing_it(monkeypatch):
    item = MANIFEST["assignments"][0]
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), delete=AsyncMock(), commit=AsyncMock())
    service = LessonCodeContentService(db)
    service._snapshot = AsyncMock(return_value=("1/4/100.md", None, [], "a" * 64))
    service.get = AsyncMock(return_value="saved")
    runner = AsyncMock(side_effect=AssertionError("Эталон самопроверки не должен выполняться"))
    monkeypatch.setattr(content_module, "execute_code", runner)
    monkeypatch.setattr(content_module.minio_storage, "put_stream", AsyncMock())
    request = LessonCodeContentRequest(content=":::code sql\nid: fixture\n:::", version="a" * 64,
        solutions=[CodeSolution(exercise_id="fixture", language="sql", code=item["code"], check_mode="self_review")])
    assert asyncio.run(service.save(100, request)) == "saved"
    runner.assert_not_awaited()
    saved = json.loads(db.add.call_args.args[0].answer)
    assert saved["check_mode"] == "self_review" and saved["value"] == item["code"]
    assert "execution" not in saved


def test_existing_python_mode_is_not_changed():
    assert CodeSolution(exercise_id="fixture", language="python", code="print(1)").check_mode == "graded"
    with pytest.raises(ValueError):
        CodeSolution(exercise_id="fixture", language="python", code="print(1)", check_mode="self_review")
