"""Реальные транзакции/квоты в отдельной временной схеме, без запросов к DeepSeek.

AI_POSTGRES_TESTS=1 venv/bin/python -m pytest tests/test_ai_postgres.py -q
Используется текущий PostgreSQL, но public и данные приложения не меняются.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import asyncpg
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.schemas.ai import AIQuestionRequest
from app.api.v1.services import ai as module
from app.api.v1.services.ai import LessonAIService
from app.core.config import settings
from app.models.ai import AIAnswer, AIConversation, AIQuestion
from app.services.llm.deepseek import MentorResult

pytestmark = pytest.mark.skipif(os.getenv("AI_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
MIGRATION = Path(__file__).resolve().parents[1] / "infra/postgres/core_db/migrations/V9__lesson_ai.sql"


@asynccontextmanager
async def database():
    schema = "test_ai_" + uuid4().hex
    admin = await asyncpg.connect(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
    engine = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await admin.execute("""
            CREATE TABLE users (user_id INTEGER PRIMARY KEY);
            CREATE TABLE lessons (lesson_id INTEGER PRIMARY KEY);
            INSERT INTO users VALUES (1), (2);
            INSERT INTO lessons VALUES (1), (2);
        """)
        await admin.execute(MIGRATION.read_text())
        await admin.execute(MIGRATION.with_name("V10__ai_provider_sessions.sql").read_text())
        engine = create_async_engine(settings.database_url, connect_args={"server_settings": {"search_path": schema}})
        yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    finally:
        if engine is not None:
            await engine.dispose()
        await admin.execute('SET search_path TO public')
        await admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await admin.close()


def current(user_id=1):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


def service(db):
    instance = LessonAIService(db)
    instance._access = AsyncMock(return_value=(
        SimpleNamespace(course_id=1, title="SQL", description="Учебный курс"),
        SimpleNamespace(title="Запросы"), SimpleNamespace(lesson_id=1, title="GROUP BY"), {},
    ))
    instance._read_content = AsyncMock(return_value=SimpleNamespace(content="Публичный урок " * 1000))
    return instance


def request(question="Как работает GROUP BY?", request_id=None):
    return AIQuestionRequest(request_id=request_id or uuid4(), question=question, user_context="Новичок")


@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setenv("MODEL", "deepseek-flash")
    monkeypatch.setenv("DEEPSEEK_USER_DAILY_LIMIT", "50")
    monkeypatch.setenv("DEEPSEEK_USER_MINUTE_LIMIT", "5")
    monkeypatch.setenv("DEEPSEEK_PROJECT_MINUTE_LIMIT", "10")
    monkeypatch.setenv("DEEPSEEK_PROJECT_DAILY_LIMIT", "200")


def test_storage_context_idempotency_and_user_lesson_isolation(monkeypatch):
    async def scenario():
        async with database() as sessions:
            snapshots = []

            async def generate(config, system, context):
                # Вопрос действительно уже виден другому соединению до обращения к модели.
                async with sessions() as check:
                    assert (await check.scalar(select(func.count()).select_from(AIQuestion))) == len(snapshots) + 1
                snapshots.append(context)
                return MentorResult("completed", "Объяснение GROUP BY", "Нужна помощь с группировкой",
                                    raw={"audit_only": "provider raw"}, input_tokens=100, output_tokens=20,
                                    model=config.model)

            generator = AsyncMock(side_effect=generate)
            monkeypatch.setattr(module, "generate", generator)
            first = request()
            async with sessions() as db:
                response = await service(db).ask(object(), "sql", 1, 1, current(), first)
                assert response.status == "completed"
                assert "audit_only" not in response.model_dump_json()
            async with sessions() as db:
                repeated = await service(db).ask(object(), "sql", 1, 1, current(), first)
                assert repeated.question_id == response.question_id
                assert generator.await_count == 1
                with pytest.raises(HTTPException) as exc:
                    await service(db).ask(object(), "sql", 1, 1, current(), request("Другой вопрос", first.request_id))
                assert exc.value.status_code == 409
            async with sessions() as db:
                await service(db).ask(object(), "sql", 1, 1, current(), request("А что делает COUNT?"))
            assert snapshots[0]["summary"] == ""
            assert snapshots[1]["summary"] == "Нужна помощь с группировкой"
            assert snapshots[1]["history"] == [{"question": first.question, "answer": "Объяснение GROUP BY"}]
            assert len(snapshots[1]["lesson"]["text"]) <= module.LESSON_CHARS
            assert snapshots[1]["lesson"]["text_truncated"]
            async with sessions() as db:
                mentor = service(db)
                own = await mentor.history(object(), "sql", 1, 1, current(), limit=1)
                assert len(own.messages) == 1 and own.next_after_id == response.question_id
                rest = await mentor.history(object(), "sql", 1, 1, current(), after_id=own.next_after_id)
                assert len(rest.messages) == 1 and rest.next_after_id is None
                assert not (await mentor.history(object(), "sql", 1, 1, current(2))).messages
                assert not (await mentor.history(object(), "sql", 1, 2, current())).messages
                answers = (await db.scalars(select(AIAnswer))).all()
                assert len(answers) == 2 and answers[0].provider_response == {"audit_only": "provider raw"}
                assert answers[0].input_tokens == 100
                assert all(q.model == "deepseek-flash" for q in (await db.scalars(select(AIQuestion))).all())
    asyncio.run(scenario())


@pytest.mark.parametrize("status", ["refused", "failed", "cancelled"])
def test_failure_audit_does_not_poison_summary_and_releases_lease(monkeypatch, status):
    async def scenario():
        async with database() as sessions:
            if status == "cancelled":
                generate = AsyncMock(side_effect=asyncio.CancelledError())
            else:
                generate = AsyncMock(return_value=MentorResult(status, "Безопасный ответ", "injected summary"))
            monkeypatch.setattr(module, "generate", generate)
            data = request()
            async with sessions() as db:
                if status == "cancelled":
                    with pytest.raises(asyncio.CancelledError):
                        await service(db).ask(object(), "sql", 1, 1, current(), data)
                else:
                    response = await service(db).ask(object(), "sql", 1, 1, current(), data)
                    assert response.status == status
            async with sessions() as db:
                conversation = (await db.scalars(select(AIConversation))).one()
                assert conversation.summary == "" and conversation.active_request is None
                question = (await db.scalars(select(AIQuestion))).one()
                assert question.status == ("failed" if status == "cancelled" else status)
                assert (await db.scalars(select(AIAnswer))).one().question_id == question.question_id
    asyncio.run(scenario())


def test_parallel_requests_do_not_duplicate_upstream_calls(monkeypatch):
    async def scenario():
        async with database() as sessions:
            started, release = asyncio.Event(), asyncio.Event()

            async def generate(*args):
                started.set()
                await release.wait()
                return MentorResult("completed", "Ответ", "Краткая память")

            mock = AsyncMock(side_effect=generate)
            monkeypatch.setattr(module, "generate", mock)
            data = request()

            async def first():
                async with sessions() as db:
                    return await service(db).ask(object(), "sql", 1, 1, current(), data)

            task = asyncio.create_task(first())
            try:
                await asyncio.wait_for(started.wait(), 5)
                async with sessions() as db:
                    repeated = await service(db).ask(object(), "sql", 1, 1, current(), data)
                    assert repeated.status == "pending"
                async with sessions() as db:
                    with pytest.raises(HTTPException) as exc:
                        await service(db).ask(object(), "sql", 1, 1, current(), request())
                    assert exc.value.detail["code"] == "AI_REQUEST_IN_PROGRESS"
            finally:
                release.set()
            assert (await task).status == "completed"
            assert mock.await_count == 1
    asyncio.run(scenario())


@pytest.mark.parametrize("quota", ["DEEPSEEK_USER_DAILY_LIMIT", "DEEPSEEK_USER_MINUTE_LIMIT"])
def test_quota_is_shared_across_lessons(monkeypatch, quota):
    monkeypatch.setenv(quota, "1")
    mock = AsyncMock(return_value=MentorResult("completed", "Ответ", "Память"))
    monkeypatch.setattr(module, "generate", mock)

    async def scenario():
        async with database() as sessions:
            data = request()
            async with sessions() as db:
                await service(db).ask(object(), "sql", 1, 1, current(), data)
            async with sessions() as db:
                await service(db).ask(object(), "sql", 1, 1, current(), data)  # повтор бесплатен
            async with sessions() as db:
                with pytest.raises(HTTPException) as exc:
                    await service(db).ask(object(), "sql", 1, 2, current(), request())
                assert exc.value.status_code == 429
            async with sessions() as db:
                await service(db).ask(object(), "sql", 1, 1, current(2), request())
            assert mock.await_count == 2
    asyncio.run(scenario())


def test_expired_request_can_be_recovered_without_duplicate_billing(monkeypatch):
    async def scenario():
        async with database() as sessions:
            data = request()
            # Имитируем аварийное завершение после фиксации вопроса.
            async with sessions() as db:
                conversation = AIConversation(user_id=1, lesson_id=1, active_request=data.request_id,
                                              busy_until=datetime.now(timezone.utc) - timedelta(seconds=1))
                db.add(conversation)
                await db.flush()
                db.add(AIQuestion(conversation_id=conversation.conversation_id, request_id=data.request_id,
                                  question=data.question, user_context=data.user_context,
                                  context_snapshot={}, prompt_hash="a" * 64, model="test", status="pending"))
                await db.commit()
            mock = AsyncMock()
            monkeypatch.setattr(module, "generate", mock)
            async with sessions() as db:
                response = await service(db).ask(object(), "sql", 1, 1, current(), data)
                assert response.status == "failed" and response.answer
                mock.assert_not_awaited()
                assert (await db.scalars(select(AIAnswer))).one().error_code == "AI_REQUEST_EXPIRED"
    asyncio.run(scenario())


def test_local_session_survives_service_recreation_and_new_lesson_starts_empty(monkeypatch):
    contexts = []

    async def generate(config, system, context):
        contexts.append(context)
        return MentorResult("completed", "Учебный ответ", "Краткая память", model=config.model)

    monkeypatch.setattr(module, "generate", generate)

    async def scenario():
        async with database() as sessions:
            for lesson_id in (1, 1, 2):
                # New SQLAlchemy session/service as on a browser refresh/another worker.
                async with sessions() as db:
                    await service(db).ask(object(), "sql", 1, lesson_id, current(), request())
            assert contexts[0]["summary"] == contexts[2]["summary"] == ""
            assert contexts[0]["brief_context"] == contexts[2]["brief_context"]
            assert contexts[0]["brief_context"]
            assert contexts[0]["history"] == contexts[2]["history"] == []
            assert contexts[1]["summary"] == "Краткая память"
            assert len(contexts[1]["history"]) == 1
            async with sessions() as db:
                conversations = (await db.scalars(select(AIConversation))).all()
                assert len(conversations) == 2
                assert all(item.provider_state["provider"] == "deepseek" for item in conversations)
                assert all("id" not in item.provider_state for item in conversations)
    asyncio.run(scenario())


def test_project_quota_is_shared_between_users(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_PROJECT_MINUTE_LIMIT", "1")
    generator = AsyncMock(return_value=MentorResult("completed", "Ответ", "Память"))
    monkeypatch.setattr(module, "generate", generator)

    async def scenario():
        async with database() as sessions:
            async with sessions() as db:
                await service(db).ask(object(), "sql", 1, 1, current(1), request())
            async with sessions() as db:
                with pytest.raises(HTTPException) as exc:
                    await service(db).ask(object(), "sql", 1, 1, current(2), request())
                assert exc.value.detail["code"] == "AI_PROJECT_QUOTA_EXCEEDED"
            assert generator.await_count == 1
    asyncio.run(scenario())
