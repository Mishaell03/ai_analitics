"""ТЕСТЫ ПОДТВЕРЖДЕНИЯ ПРОХОЖДЕНИЯ УРОКА."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI

from app.api.v1.routes import lesson_completion as route_module
from app.api.v1.services.lesson_content import LessonContentService
from app.api.v1.services.lesson_completion import LessonCompletionService
from app.core.database import get_db
from app.core.session import get_current_user
from app.models.enrollments_progress import COMPLETED_CORRECTNESS, LessonAttempt
from app.models.enrollments_progress import PASSED_EXERCISES_KEY


def test_get_exercise_ids_only_uses_test_blocks_with_ids():
    blocks = [
        SimpleNamespace(type="test", data={"exercise_id": "test-1"}),
        SimpleNamespace(type="video", data={"exercise_id": "video-1"}),
        SimpleNamespace(type="test", data={"exercise_id": None}),
        SimpleNamespace(type="test", data={"exercise_id": "test-2"}),
    ]

    assert LessonCompletionService.get_exercise_ids(blocks) == {"test-1", "test-2"}


def test_lesson_content_only_returns_successful_exercise_answers():
    attempts = [
        SimpleNamespace(
            answers={PASSED_EXERCISES_KEY: {"test-1": '{"type":"text","value":"ok"}'}},
            correctness=2,
        ),
        SimpleNamespace(answers={"failed-test": "wrong"}, correctness=1),
        SimpleNamespace(answers={"legacy-test": "old answer"}, correctness=3),
    ]

    assert LessonContentService._merge_completed_exercises(attempts) == {
        "test-1": '{"type":"text","value":"ok"}',
        "legacy-test": "old answer",
    }


@pytest.mark.parametrize(
    ("required", "passed", "expected"),
    [
        ({"test-1", "test-2"}, {"test-1": "answer"}, False),
        ({"test-1", "test-2"}, {"test-1": "answer", "test-2": "answer"}, True),
        (set(), {}, True),
    ],
)
def test_all_exercises_passed(required, passed, expected):
    assert LessonCompletionService.all_exercises_passed(required, passed) is expected


@pytest.mark.parametrize(
    ("passed", "should_complete"),
    [
        ({"test-1": "answer"}, False),
        ({"test-1": "answer", "test-2": "answer"}, True),
    ],
)
def test_completion_persists_only_after_every_test(monkeypatch, passed, should_complete):
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                scalar_one_or_none=Mock(return_value=None)
            )
        ),
        add=Mock(),
        commit=AsyncMock(),
    )
    service = LessonCompletionService(db)
    content = SimpleNamespace(
        custom_blocks=[
            SimpleNamespace(type="test", data={"exercise_id": "test-1"}),
            SimpleNamespace(type="test", data={"exercise_id": "test-2"}),
        ],
        completed_exercises=passed,
    )

    async def get_content(self, **kwargs):
        return content

    monkeypatch.setattr(
        "app.api.v1.services.lesson_completion.LessonContentService.get_lesson_content",
        get_content,
    )

    async def scenario():
        return await service.complete_lesson(
            request=object(),
            course_slug="course",
            module_id=2,
            lesson_id=3,
            language="en",
            user_id=123,
        )

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert result is should_complete
    if should_complete:
        attempt = db.add.call_args.args[0]
        assert isinstance(attempt, LessonAttempt)
        assert attempt.correctness == COMPLETED_CORRECTNESS
        assert attempt.answers == passed
        db.commit.assert_awaited_once()
    else:
        db.add.assert_not_called()
        db.commit.assert_not_awaited()


def test_completion_route_returns_boolean_json(monkeypatch):
    app = FastAPI()
    app.include_router(route_module.router, prefix="/api/v1")
    current = SimpleNamespace(
        user=SimpleNamespace(user_id=123),
        session=SimpleNamespace(
            language="en",
            device_id="test-device",
            id=5,
            platform="web",
        ),
    )
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user] = lambda: current

    async def complete_lesson(self, **kwargs):
        return True

    async def no_event(**kwargs):
        return None

    monkeypatch.setattr(LessonCompletionService, "complete_lesson", complete_lesson)
    monkeypatch.setattr(route_module, "user_event_logs", no_event)

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            return await client.post(
                "/api/v1/courses/demo/modules/2/lessons/3/complete"
            )

    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(scenario())
    finally:
        loop.close()

    assert response.status_code == 200
    assert response.json() is True
