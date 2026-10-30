"""Контракт HTTP, доступ и grading без подключения к прикладной БД."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI, HTTPException

from app.api.v1.routes.student_exercises import router
from app.api.v1.routes.sandbox import router as sandbox_router
from app.api.v1.schemas.sandbox import ExecutionResult, SandboxExecuteRequest
from app.api.v1.services import sandbox as sandbox_module
from app.api.v1.services.sandbox import SandboxService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.database import get_db
from app.core.exception_handlers import RequestBodyMiddleware
from app.core.markdown import MarkdownParser
from app.core.session import get_current_user
from app.models.enrollments_progress import PASSED_EXERCISES_KEY
from app.services.sandbox.config import MAX_REQUEST_BYTES

PATH = "/api/v1/courses/python/modules/2/lessons/3/exercises"


@pytest.fixture
def current():
    return SimpleNamespace(user=SimpleNamespace(user_id=7), session=SimpleNamespace(
        language="en", device_id="d", id=1, platform="web",
    ))


@pytest.fixture(autouse=True)
def sandbox_config(monkeypatch):
    monkeypatch.setenv("SANDBOX_ASSIGNMENT_PROFILES", '{"3:py-1":"light"}')
    sandbox_module.execution_limiter.reset()


def submission(language="python", code="print(42)"):
    return SandboxExecuteRequest(
        course_slug="python", module_id=2, lesson_id=3,
        exercise_id="py-1", language=language, code=code,
    )


def content(language="python", completed=None):
    parsed = MarkdownParser().parse(
        f":::test\nid: py-1\nlanguage: {language}\nPrint 42.\n:::\n"
    )
    return SimpleNamespace(custom_blocks=parsed.custom_blocks, completed_exercises=completed or {})


@pytest.mark.parametrize("language", ["python", "sql"])
def test_list_only_public_fields_and_own_progress(current, language):
    service = StudentExerciseService(None)
    service.get_lesson_content = AsyncMock(return_value=content(language, {"py-1": "own code"}))
    exercises = asyncio.run(service.list_exercises(object(), "python", 2, 3, current))
    assert exercises[0].model_dump() == {
        "exercise_id": "py-1", "body": "Print 42.", "language": language,
        "execution_enabled": True, "is_completed": True,
        "expert_solution_available": True,
    }
    assert service.get_lesson_content.call_args.kwargs["user_id"] == 7
    assert "is_admin" not in service.get_lesson_content.call_args.kwargs


@pytest.mark.parametrize("failure", ["course", "module", "lesson", "enrollment"])
def test_real_content_access_checks_precede_storage(current, failure):
    service = StudentExerciseService(None)
    service._get_course = AsyncMock(return_value=SimpleNamespace(course_id=1))
    service._get_module = AsyncMock(return_value=SimpleNamespace(module_id=2))
    service._get_lesson = AsyncMock(return_value=SimpleNamespace(lesson_id=3))
    service._is_enrolled = AsyncMock(return_value=failure != "enrollment")
    service._read_content = AsyncMock()
    service._raise = AsyncMock(side_effect=HTTPException(403))
    if failure != "enrollment":
        getattr(service, f"_get_{failure}").side_effect = HTTPException(404)
    with pytest.raises(HTTPException):
        asyncio.run(service.list_exercises(object(), "python", 2, 3, current))
    service._read_content.assert_not_awaited()


def test_deleted_and_duplicate_exercises_fail_closed(current):
    service = StudentExerciseService(None)
    service.get_lesson_content = AsyncMock(return_value=content())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_exercise(object(), "python", 2, 3, "reference", current))
    assert exc.value.status_code == 404
    duplicate = content()
    duplicate.custom_blocks *= 2
    service.get_lesson_content.return_value = duplicate
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.list_exercises(object(), "python", 2, 3, current))
    assert exc.value.status_code == 409


@pytest.mark.parametrize("configured,requested,status", [
    ("python", "sql", 422), ("sql", "python", 422),
    (None, "python", 422),
])
@pytest.mark.parametrize("code", ["SELECT 1", "DROP TABLE users", "SELECT pg_read_file('/etc/passwd')"])
def test_language_mismatch_never_reaches_runner(monkeypatch, current, configured, requested, status, code):
    monkeypatch.setattr(StudentExerciseService, "get_exercise", AsyncMock(
        return_value=SimpleNamespace(language=configured)))
    execute = AsyncMock()
    monkeypatch.setattr(sandbox_module, "execute_code", execute)
    db = SimpleNamespace(execute=AsyncMock(), add=Mock(), commit=AsyncMock())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(SandboxService(db).submit(object(), submission(requested, code), current))
    assert exc.value.status_code == status
    execute.assert_not_awaited()
    db.execute.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.parametrize("flags,expected,correct", [
    ({}, "42\n", True), ({}, "43\n", False),
    ({"exit_code": 1, "stderr": "SyntaxError"}, "42\n", False),
    ({"timed_out": True}, "42\n", False),
    ({"memory_limited": True}, "42\n", False),
    ({"output_limited": True}, "42\n", False),
])
def test_submission_grades_only_success_and_records_own_attempt(monkeypatch, current, flags, expected, correct):
    monkeypatch.setattr(StudentExerciseService, "get_exercise", AsyncMock(
        return_value=SimpleNamespace(language="python")))
    execution = ExecutionResult(**dict(
        {"stdout": "42\n", "stderr": "", "exit_code": 0, "timed_out": False, "duration": 0.1}, **flags))
    execute = AsyncMock(return_value=execution)
    monkeypatch.setattr(sandbox_module, "execute_code", execute)
    reference = json.dumps({"type": "code", "language": "python", "value": "print(6 * 7)",
                            "execution": {"stdout": expected, "stderr": "", "exit_code": 0,
                                          "timed_out": False, "duration": 0.1}})
    rows = [SimpleNamespace(scalar_one_or_none=lambda: reference)]
    db = SimpleNamespace(execute=AsyncMock(side_effect=rows), add=Mock(), commit=AsyncMock())

    async def commit():
        db.add.call_args.args[0].attempt_id = 123

    db.commit.side_effect = commit
    response = asyncio.run(SandboxService(db).submit(object(), submission(), current))
    assert response.is_correct is correct
    assert response.success == (not flags)
    assert response.execution_succeeded == (not flags)
    assert response.attempt_id == 123
    attempt = db.add.call_args.args[0]
    assert attempt.user_id == 7 and attempt.lesson_id == 3
    assert attempt.correctness == (2 if correct else 0)
    assert (PASSED_EXERCISES_KEY in attempt.answers) == bool(correct)
    execute.assert_awaited_once_with(code="print(42)", profile="light", language="python")
    assert "print(6 * 7)" not in response.model_dump_json()


def test_runner_failure_does_not_record_attempt(monkeypatch, current):
    service = SandboxService(SimpleNamespace(add=Mock(), commit=AsyncMock()))
    service.execute = AsyncMock(side_effect=HTTPException(503, detail="Sandbox unavailable"))
    with pytest.raises(HTTPException):
        asyncio.run(service.submit(object(), submission(), current))
    service.db.add.assert_not_called()
    service.db.commit.assert_not_awaited()


@pytest.mark.parametrize("language,code", [
    ("python", 'print("hello world")'),
    ("sql", "SELECT * FROM customers LIMIT 1"),
])
def test_execute_without_teacher_answer(monkeypatch, current, language, code):
    app = FastAPI()
    app.include_router(sandbox_router, prefix="/api/v1")
    # Отсутствие эталона не запрещает запуск, но не засчитывает прохождение.
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
                         add=Mock(), commit=AsyncMock())

    async def commit():
        db.add.call_args.args[0].attempt_id = 123

    db.commit.side_effect = commit
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: current
    parsed = MarkdownParser().parse(f":::code {language}\nid: py-1\n:::")
    monkeypatch.setattr(StudentExerciseService, "get_lesson_content", AsyncMock(return_value=SimpleNamespace(
        custom_blocks=parsed.custom_blocks, completed_exercises={},
    )))
    runner = AsyncMock(return_value=ExecutionResult(
        stdout="result", stderr="", exit_code=0, timed_out=False, duration=0.1,
    ))
    monkeypatch.setattr(sandbox_module, "execute_code", runner)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sandbox/execute", json=submission(language, code).model_dump())
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["stdout"] == "result"
        assert response.json()["is_correct"] is None
        assert PASSED_EXERCISES_KEY not in db.add.call_args.args[0].answers
        runner.assert_awaited_once_with(code=code, profile="light", language=language)
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    asyncio.run(scenario())


def test_execution_rate_limit_is_user_scoped(monkeypatch, current):
    monkeypatch.setattr(StudentExerciseService, "get_exercise", AsyncMock(
        return_value=SimpleNamespace(language="python")))
    execute = AsyncMock()
    monkeypatch.setattr(sandbox_module, "execute_code", execute)
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: 1)))
    for _ in range(10):
        sandbox_module.execution_limiter.allow("7")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(SandboxService(db).execute(object(), submission(), current))
    assert exc.value.status_code == 429
    execute.assert_not_awaited()
    current.user.user_id = 8
    asyncio.run(SandboxService(db).execute(object(), submission(), current))
    execute.assert_awaited_once()


@pytest.mark.parametrize("method,suffix", [("GET", ""), ("GET", "/py-1"), ("POST", "/py-1/submit")])
def test_routes_require_authentication(method, suffix):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: None

    async def denied():
        raise HTTPException(401)

    app.dependency_overrides[get_current_user] = denied

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.request(method, PATH + suffix, json={"code": "pass", "language": "python"})
        assert response.status_code == 401

    asyncio.run(scenario())


def test_http_validation_body_limit_and_public_response(monkeypatch, current):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_middleware(RequestBodyMiddleware)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: current
    monkeypatch.setattr(StudentExerciseService, "get_lesson_content", AsyncMock(return_value=content()))
    submit = AsyncMock()
    monkeypatch.setattr(SandboxService, "submit", submit)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(PATH)
            assert response.status_code == 200
            assert response.json()[0]["language"] == "python"
            for body in ({"code": "pass", "language": "javascript"},
                         {"code": " ", "language": "python"},
                         {"code": "pass", "language": "python", "user_id": 8},
                         {"code": "pass", "language": "python", "profile": "heavy"}):
                response = await client.post(PATH + "/py-1/submit", json=body)
                assert response.status_code == 422
            response = await client.post(PATH + "/py-1/submit", content=b"x" * (MAX_REQUEST_BYTES + 1))
            assert response.status_code == 413
        submit.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize("endpoint", ["submit", "execute"])
@pytest.mark.parametrize("language", ["python", "sql"])
def test_http_submission_uses_path_and_session_identity(monkeypatch, current, endpoint, language):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.include_router(sandbox_router, prefix="/api/v1")
    monkeypatch.setenv("SANDBOX_ASSIGNMENT_PROFILES", "{}")
    output = "42\n" if language == "python" else '{"columns":["count"],"rows":[[42]]}'
    reference = json.dumps({"type": "code", "language": language, "value": "TEACHER_CODE",
                            "execution": {"stdout": output, "stderr": "", "exit_code": 0,
                                          "timed_out": False, "duration": 0.1}})
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        scalar_one_or_none=lambda: reference,
    )), add=Mock(), commit=AsyncMock())

    async def commit():
        db.add.call_args.args[0].attempt_id = 99

    db.commit.side_effect = commit
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: current
    get_content = AsyncMock(return_value=content(language))
    monkeypatch.setattr(StudentExerciseService, "get_lesson_content", get_content)
    monkeypatch.setattr(sandbox_module, "execute_code", AsyncMock(return_value=ExecutionResult(
        stdout=output, stderr="", exit_code=0, timed_out=False, duration=0.1,
    )))

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            if endpoint == "submit":
                response = await client.post(PATH + "/py-1/submit", json={"language": language, "code": "print(42)"})
            else:
                response = await client.post("/api/v1/sandbox/execute", json=submission(language).model_dump())
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["is_correct"] is True
        assert "TEACHER_CODE" not in response.text
        if endpoint == "submit":
            assert response.json()["execution_succeeded"] is True
            assert response.json()["attempt_id"] == 99
        else:
            assert response.json()["stdout"] == output
        db.commit.assert_awaited_once()
        assert "answer" not in response.json()
        assert get_content.call_args.kwargs["user_id"] == 7
        assert get_content.call_args.kwargs["lesson_id"] == 3

    asyncio.run(scenario())


@pytest.mark.parametrize("header", ["language: javascript", "language: Python", "", "language: python\nlanguage: sql"])
def test_language_is_not_inferred_from_code(header):
    parsed = MarkdownParser().parse(f":::test\nid: py-1\n{header}\nSELECT 1\n:::\n")
    # Дополнительный текст не может переключить уже выбранный язык.
    expected = "python" if header.startswith("language: python\n") else None
    assert parsed.custom_blocks[0].data.get("language") == expected
