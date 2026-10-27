"""ТЕСТЫ ПРОВЕРКИ ОТВЕТА НА ОДНО ЗАДАНИЕ."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI

from app.api.v1.routes import exercise_check as route_module
from app.api.v1.services.exercise_check import ExerciseCheckService
from app.api.v1.schemas.exercise_check import ExerciseCheckRequest
from app.models.enrollments_progress import (
    LessonAttempt,
    PASSED_EXERCISE_CORRECTNESS,
    PASSED_EXERCISES_KEY,
)
from app.core.database import get_db
from app.core.session import get_current_user


@pytest.mark.parametrize(
    ("submitted", "expected", "result"),
    [
        ('{"type":"text","value":"hello"}', '{"type":"text","value":"hello"}', True),
        ('{"type":"text","value":"Hello"}', '{"type":"text","value":"hello"}', False),
        ('{"type":"code","value":"print(1)"}', '{"type":"code","value":"print(1)"}', True),
        ('{"type":"choice","correct":["A","B"]}', '{"type":"choice","correct":["B","A"]}', True),
        ('{"type":"choice","correct":["A"]}', '{"type":"choice","correct":["A","B"]}', False),
        ('{"type":"text","value":"hello"}', '{"type":"code","value":"hello"}', False),
        ("legacy", "legacy", True),
        ("other", "legacy", False),
        ('{"type":"text","value":"legacy"}', "legacy", True),
        ('{"type":"choice","correct":["A"]}', "A", False),
    ],
)
def test_answers_match(submitted, expected, result):
    assert ExerciseCheckService.answers_match(submitted, expected) is result


def test_route_returns_boolean_json(monkeypatch):
    app = FastAPI()
    app.include_router(route_module.router, prefix="/api/v1")
    fake_user = SimpleNamespace(
        user=SimpleNamespace(user_id=123),
        session=SimpleNamespace(
            language="en",
            device_id="test-device",
            id=5,
            platform="web",
        ),
    )
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user] = lambda: fake_user

    async def check_answer(self, **kwargs):
        return kwargs["data"].answer == "correct"

    async def no_event(**kwargs):
        return None

    monkeypatch.setattr(ExerciseCheckService, "check_answer", check_answer)
    monkeypatch.setattr(route_module, "user_event_logs", no_event)

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            correct = await client.post(
                "/api/v1/courses/demo/modules/2/lessons/3/exercises/ex-1/check",
                json={"answer": "correct"},
            )
            incorrect = await client.post(
                "/api/v1/courses/demo/modules/2/lessons/3/exercises/ex-1/check",
                json={"answer": "wrong"},
            )
        return correct, incorrect

    loop = asyncio.new_event_loop()
    try:
        correct, incorrect = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert correct.status_code == 200
    assert correct.json() is True
    assert incorrect.status_code == 200
    assert incorrect.json() is False


def test_request_requires_a_single_nonempty_answer():
    from app.api.v1.schemas.exercise_check import ExerciseCheckRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExerciseCheckRequest(answer="")


@pytest.mark.parametrize(
    ("submitted", "is_correct"),
    [
        ('{"type":"text","value":"hello"}', True),
        ('{"type":"text","value":"wrong"}', False),
    ],
)
def test_check_persists_only_successful_answers(monkeypatch, submitted, is_correct):
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one_or_none=Mock(return_value=1)),
                SimpleNamespace(
                    scalar_one_or_none=Mock(
                        return_value='{"type":"text","value":"hello"}'
                    )
                ),
            ]
        ),
        add=Mock(),
        commit=AsyncMock(),
    )
    service = ExerciseCheckService(db)

    async def get_course(**kwargs):
        return SimpleNamespace(course_id=7)

    async def get_module(**kwargs):
        return SimpleNamespace(module_id=8)

    async def get_lesson(**kwargs):
        return SimpleNamespace(lesson_id=9)

    monkeypatch.setattr(service, "_get_course", get_course)
    monkeypatch.setattr(service, "_get_module", get_module)
    monkeypatch.setattr(service, "_get_lesson", get_lesson)

    async def scenario():
        return await service.check_answer(
            request=object(),
            course_slug="course",
            module_id=8,
            lesson_id=9,
            exercise_id="exercise-1",
            data=ExerciseCheckRequest(answer=submitted),
            language="en",
            user_id=123,
        )

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert result is is_correct
    if is_correct:
        stored_attempt = db.add.call_args.args[0]
        assert isinstance(stored_attempt, LessonAttempt)
        assert stored_attempt.user_id == 123
        assert stored_attempt.lesson_id == 9
        assert stored_attempt.answers == {
            PASSED_EXERCISES_KEY: {"exercise-1": submitted}
        }
        assert stored_attempt.correctness == PASSED_EXERCISE_CORRECTNESS
        db.commit.assert_awaited_once()
    else:
        db.add.assert_not_called()
        db.commit.assert_not_awaited()
