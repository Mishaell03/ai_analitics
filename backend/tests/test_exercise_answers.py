"""Тесты правильных ответов на задания: сервис и API.

Интеграционные тесты нуждаются в поднятых PostgreSQL и MinIO.
Если их нет — тесты пропускаются.
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select

import app.main  # noqa: F401  (регистрация всех моделей)

from app.api.v1.services.exercise_answers import ExerciseAnswerService
from app.core.database import AsyncSessionLocal
from app.models.auth import UserSession
from app.models.exercises import ExerciseAnswer

from conftest import LOOP, infrastructure_available

ADMIN_USER_ID = 1000002
NOT_ADMIN_USER_ID = 1000000

LESSON_ID = 1
EXERCISE_ID = "python-variables"


def run(coroutine):
    """ЗАПУСКАЕТ КОРУТИНУ В СИНХРОННОМ ТЕСТЕ"""

    return LOOP.run_until_complete(coroutine)


def make_request():
    """ЗАПРОС ДЛЯ СЕРВИСА"""

    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": [(b"host", b"test")],
        "client": ("127.0.0.1", 12345),
        "query_string": b"",
    }

    request = Request(scope)
    request.state.raw_body = None

    return request


pytestmark = pytest.mark.skipif(
    not infrastructure_available(),
    reason="нужна поднятая PostgreSQL",
)


@pytest.fixture
def clean_answers():
    """УБИРАЕТ ОТВЕТЫ, СОЗДАННЫЕ ТЕСТАМИ"""

    exercise_ids = [EXERCISE_ID, "second-exercise"]

    yield exercise_ids

    async def cleanup():
        async with AsyncSessionLocal() as db:
            for exercise_id in exercise_ids:
                result = await db.execute(
                    select(ExerciseAnswer).where(
                        ExerciseAnswer.lesson_id == LESSON_ID,
                        ExerciseAnswer.exercise_id == exercise_id,
                    )
                )

                answer = result.scalar_one_or_none()

                if answer is not None:
                    await db.delete(answer)

            await db.commit()

    run(cleanup())


def set_answer(exercise_id: str, answer: str, user_id: int = ADMIN_USER_ID):
    """СОХРАНЯЕТ ПРАВИЛЬНЫЙ ОТВЕТ ЧЕРЕЗ СЕРВИС"""

    from app.api.v1.schemas.exercises import ExerciseAnswerRequest

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).set_answer(
                request=make_request(),
                lesson_id=LESSON_ID,
                exercise_id=exercise_id,
                data=ExerciseAnswerRequest(answer=answer),
                language="en",
                user_id=user_id,
            )

    return run(scenario())


def test_set_answer_creates_record(clean_answers):
    """СОХРАНЕНИЕ ОТВЕТА СОЗДАЁТ ЗАПИСЬ"""

    answer = set_answer(EXERCISE_ID, "print")

    assert answer.lesson_id == LESSON_ID
    assert answer.exercise_id == EXERCISE_ID
    assert answer.answer == "print"
    assert answer.answer_id > 0


def test_set_answer_updates_existing_record(clean_answers):
    """ПОВТОРНОЕ СОХРАНЕНИЕ ОБНОВЛЯЕТ ТОТ ЖЕ ЗАПИСЬ"""

    created = set_answer(EXERCISE_ID, "print")
    updated = set_answer(EXERCISE_ID, "print(value)")

    assert updated.answer_id == created.answer_id
    assert updated.answer == "print(value)"


def test_answers_are_isolated_by_lesson(clean_answers):
    """ОТВЕТЫ РАЗНЫХ УРОКОВ НЕ СМЕШИВАЮТСЯ"""

    set_answer(EXERCISE_ID, "print")

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).list_answers(
                request=make_request(),
                lesson_id=2,
                language="en",
                user_id=ADMIN_USER_ID,
            )

    other_lesson = run(scenario())

    assert other_lesson.answers == []


def test_list_answers_of_lesson_without_exercises(clean_answers):
    """У УРОКА БЕЗ ЗАДАНИЙ ОТВЕТОВ НЕТ"""

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).list_answers(
                request=make_request(),
                lesson_id=LESSON_ID,
                language="en",
                user_id=ADMIN_USER_ID,
            )

    result = run(scenario())

    assert result.lesson_id == LESSON_ID
    assert result.answers == []


def test_delete_answer_removes_record(clean_answers):
    """УДАЛЕНИЕ ОТВЕТА УБИРАЕТ ЗАПИСЬ"""

    set_answer(EXERCISE_ID, "print")

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).delete_answer(
                request=make_request(),
                lesson_id=LESSON_ID,
                exercise_id=EXERCISE_ID,
                language="en",
                user_id=ADMIN_USER_ID,
            )

    result = run(scenario())

    assert result.success is True

    async def check():
        async with AsyncSessionLocal() as db:
            found = await db.execute(
                select(ExerciseAnswer).where(
                    ExerciseAnswer.lesson_id == LESSON_ID,
                    ExerciseAnswer.exercise_id == EXERCISE_ID,
                )
            )

            return found.scalar_one_or_none()

    assert run(check()) is None


def test_delete_missing_answer_fails(clean_answers):
    """УДАЛЕНИЕ НЕСУЩЕСТВУЮЩЕГО ОТВЕТА — ОШИБКА"""

    from fastapi import HTTPException

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).delete_answer(
                request=make_request(),
                lesson_id=LESSON_ID,
                exercise_id=EXERCISE_ID,
                language="en",
                user_id=ADMIN_USER_ID,
            )

    with pytest.raises(HTTPException) as error:
        run(scenario())

    assert error.value.detail["code"] == "EXERCISE_ANSWER_NOT_FOUND"


def test_set_answer_for_unknown_lesson_fails(clean_answers):
    """ОТВЕТ ДЛЯ НЕСУЩЕСТВУЮЩЕГО УРОКА — ОШИБКА"""

    from fastapi import HTTPException

    from app.api.v1.schemas.exercises import ExerciseAnswerRequest

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await ExerciseAnswerService(db).set_answer(
                request=make_request(),
                lesson_id=999999,
                exercise_id=EXERCISE_ID,
                data=ExerciseAnswerRequest(answer="print"),
                language="en",
                user_id=ADMIN_USER_ID,
            )

    with pytest.raises(HTTPException) as error:
        run(scenario())

    assert error.value.detail["code"] == "LESSON_NOT_FOUND"


# ---------- API ----------

@pytest.fixture
def api_client():
    """КЛИЕНТ API С СЕССИЕЙ АДМИНИСТРАТОРА"""

    from app.main import app

    token = f"test-exercise-session-{uuid.uuid4().hex[:8]}"

    async def create_session():
        async with AsyncSessionLocal() as db:
            db.add(
                UserSession(
                    user_id=ADMIN_USER_ID,
                    session=token,
                    ip="127.0.0.1",
                    language="en",
                    provider="pass",
                    platform="web",
                    device_name="pytest",
                    device_id="pytest-device",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                )
            )

            await db.commit()

    run(create_session())

    transport = httpx.ASGITransport(app=app)

    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    client.cookies.set("session_token", token)

    async def scenario():
        return await client

    yield client

    async def cleanup():
        await client.aclose()

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserSession).where(
                    UserSession.session == token,
                )
            )

            session = result.scalar_one_or_none()

            if session is not None:
                await db.delete(session)

            await db.commit()

    run(cleanup())


def test_api_creates_and_updates_answer(api_client, clean_answers):
    """API СОЗДАЁТ И ОБНОВЛЯЕТ ОТВЕТ ОДНИМ ЗАПРОСОМ"""

    async def scenario():
        created = await api_client.post(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
            json={"answer": "print"},
        )

        updated = await api_client.post(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
            json={"answer": "print(value)"},
        )

        listed = await api_client.get(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises",
        )

        return created, updated, listed

    created, updated, listed = run(scenario())

    assert created.status_code == 200
    assert created.json()["answer"] == "print"

    assert updated.status_code == 200
    assert updated.json()["answer"] == "print(value)"
    assert updated.json()["answer_id"] == created.json()["answer_id"]

    assert listed.status_code == 200
    assert len(listed.json()["answers"]) == 1


def test_api_deletes_answer(api_client, clean_answers):
    """API УДАЛЯЕТ ОТВЕТ"""

    async def scenario():
        await api_client.post(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
            json={"answer": "print"},
        )

        deleted = await api_client.delete(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
        )

        again = await api_client.delete(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
        )

        return deleted, again

    deleted, again = run(scenario())

    assert deleted.status_code == 200
    assert deleted.json()["success"] is True

    assert again.status_code == 404
    assert again.json()["detail"]["code"] == "EXERCISE_ANSWER_NOT_FOUND"


def test_api_validates_answer(api_client, clean_answers):
    """API ПРОВЕРЯЕТ ОТВЕТ И ИДЕНТИФИКАТОР ЗАДАНИЯ"""

    async def scenario():
        empty = await api_client.post(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
            json={"answer": ""},
        )

        wrong_id = await api_client.post(
            f"/api/v1/admin/lessons/{LESSON_ID}/exercises/bad%20id/answer",
            json={"answer": "print"},
        )

        return empty, wrong_id

    empty, wrong_id = run(scenario())

    assert empty.status_code == 422
    assert wrong_id.status_code == 422


def test_api_forbids_non_admin(api_client, clean_answers):
    """API НЕДОСТУПЕН НЕ-АДМИНУ"""

    from app.main import app

    async def scenario():
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )
        client.cookies.set("session_token", "seed-session-alexey-2026")

        try:
            return await client.post(
                f"/api/v1/admin/lessons/{LESSON_ID}/exercises/{EXERCISE_ID}/answer",
                json={"answer": "print"},
            )

        finally:
            await client.aclose()

    response = run(scenario())

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ADMIN_ACCESS_REQUIRED"
