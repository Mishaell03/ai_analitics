import json
from types import SimpleNamespace

import pytest

from app.api.v1.schemas.sandbox import ExecutionResult
from app.api.v1.services.sandbox import SandboxService
from app.api.v1.services.lesson_content import LessonContentService
from app.models.enrollments_progress import PASSED_EXERCISES_KEY


def execution(stdout="42\n", **kwargs):
    return ExecutionResult(**{
        "stdout": stdout, "stderr": "", "exit_code": 0,
        "timed_out": False, "duration": 0.1, **kwargs,
    })


def reference(stdout="42\n", language="python", **kwargs):
    return json.dumps({"type": "code", "language": language, "value": "TEACHER_SECRET",
                       "execution": execution(stdout, **kwargs).model_dump()})


@pytest.mark.parametrize("expected", [
    None, "legacy source", '{"type":"code","language":"python","value":"print(42)"}',
    reference(language="sql"), reference(exit_code=1), reference(timed_out=True),
    reference(output_limited=True), reference(memory_limited=True),
])
def test_missing_or_failed_reference_cannot_pass(expected):
    assert SandboxService.grade(execution(), expected, "python") is None


@pytest.mark.parametrize("actual,expected,correct", [
    ("42\n", "42\r\n", True), ("42", "42\n", True),
    ("42 ", "42", False), ("43", "42", False), ("", "", True),
])
def test_python_compares_output(actual, expected, correct):
    assert SandboxService.grade(execution(actual), reference(expected), "python") is correct


@pytest.mark.parametrize("actual,correct", [
    ({"rows": [[1], [2]], "columns": ["id"]}, True),
    ({"rows": [[2], [1]], "columns": ["id"]}, False),
    ({"rows": [[1]], "columns": ["id"]}, False),
    ({"rows": [[1], [2]], "columns": ["other"]}, False),
])
def test_sql_compares_columns_and_rows_not_json_format(actual, correct):
    expected = reference('{"columns":["id"],"rows":[[1],[2]]}', language="sql")
    assert SandboxService.grade(execution(json.dumps(actual, indent=2)), expected, "sql") is correct


def test_ungraded_runs_do_not_count_as_completed_exercises():
    attempts = [
        SimpleNamespace(correctness=2, answers={"execution": {}, PASSED_EXERCISES_KEY: {"old": "code"}}),
        SimpleNamespace(correctness=2, answers={"execution": {}, "is_correct": True,
                                               PASSED_EXERCISES_KEY: {"graded": "code"}}),
        SimpleNamespace(correctness=2, answers={PASSED_EXERCISES_KEY: {"quiz": "answer"}}),
    ]
    assert LessonContentService._merge_completed_exercises(attempts) == {"graded": "code", "quiz": "answer"}
