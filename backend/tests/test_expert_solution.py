"""Эталон выдаётся отдельным запросом только после успешного решения."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI, HTTPException

from app.api.v1.routes.student_exercises import router
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.database import get_db
from app.core.markdown import MarkdownParser
from app.core.session import get_current_user

PATH = "/api/v1/courses/demo/modules/2/lessons/3/exercises/code-1/expert-solution"
SECRET = "print('EXPERT_SECRET')"


@pytest.fixture
def current():
    return SimpleNamespace(user=SimpleNamespace(user_id=7), session=SimpleNamespace(
        language="en", device_id="d", id=1, platform="web",
    ))


def content(language="python", completed=False):
    return SimpleNamespace(
        custom_blocks=MarkdownParser().parse(f":::code {language}\nid: code-1\n:::").custom_blocks,
        completed_exercises={"code-1": "student code"} if completed else {},
    )


def database(raw=None):
    return SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=Mock(return_value=raw))),
        add=Mock(), commit=AsyncMock(),
    )


@pytest.mark.parametrize("language,code", [("python", SECRET), ("sql", "SELECT * FROM customers")])
def test_expert_solution_after_success_contains_only_code(current, language, code):
    db = database(json.dumps({"type": "code", "language": language, "value": code,
                              "execution": {"stdout": "PRIVATE_OUTPUT"}}))
    service = StudentExerciseService(db)
    service.get_lesson_content = AsyncMock(return_value=content(language, completed=True))
    response = asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current))
    assert response.model_dump() == {"exercise_id": "code-1", "language": language, "code": code}
    assert service.get_lesson_content.call_args.kwargs["user_id"] == 7
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


def test_unsolved_exercise_does_not_even_read_reference(current):
    db = database()
    service = StudentExerciseService(db)
    service.get_lesson_content = AsyncMock(return_value=content(completed=False))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current))
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "EXERCISE_NOT_COMPLETED"
    db.execute.assert_not_awaited()


@pytest.mark.parametrize("status", [403, 404])
def test_content_access_is_checked_before_expert_solution(current, status):
    db = database()
    service = StudentExerciseService(db)
    service.get_lesson_content = AsyncMock(side_effect=HTTPException(status))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current))
    assert exc.value.status_code == status
    db.execute.assert_not_awaited()


def test_other_students_progress_does_not_unlock_solution(current):
    db = database(json.dumps({"type": "code", "language": "python", "value": SECRET}))
    service = StudentExerciseService(db)

    async def get_content(**kwargs):
        return content(completed=kwargs["user_id"] == 7)

    service.get_lesson_content = AsyncMock(side_effect=get_content)
    assert asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current)).code == SECRET
    current.user.user_id = 8
    db.execute.reset_mock()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current))
    assert exc.value.status_code == 403
    db.execute.assert_not_awaited()


@pytest.mark.parametrize("raw", [
    None, "legacy code", '{"type":"choice","correct":["A"]}',
    '{"type":"code","language":"sql","value":"SELECT 1"}',
    '{"type":"code","language":"python","value":42}',
    '{"type":"code","language":"python","value":" "}',
])
def test_missing_or_invalid_reference_fails_closed(current, raw):
    service = StudentExerciseService(database(raw))
    service.get_lesson_content = AsyncMock(return_value=content(completed=True))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "code-1", current))
    assert exc.value.status_code == 404


def test_unknown_exercise_never_reads_reference(current):
    db = database()
    service = StudentExerciseService(db)
    service.get_lesson_content = AsyncMock(return_value=content(completed=True))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_expert_solution(object(), "demo", 2, 3, "other", current))
    assert exc.value.status_code == 404
    db.execute.assert_not_awaited()


@pytest.mark.parametrize("completed,status", [(False, 403), (True, 200)])
def test_expert_solution_http_contract(monkeypatch, current, completed, status):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    db = database(json.dumps({"type": "code", "language": "python", "value": SECRET}))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: current
    monkeypatch.setattr(StudentExerciseService, "get_lesson_content", AsyncMock(return_value=content(completed=completed)))

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(PATH)

    response = asyncio.run(scenario())
    assert response.status_code == status
    if completed:
        assert response.json() == {"exercise_id": "code-1", "language": "python", "code": SECRET}
        assert response.headers["cache-control"] == "private, no-store"
    else:
        assert SECRET not in response.text
