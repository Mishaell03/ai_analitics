"""Offline tests for compact backend memory, separate lesson sessions and safe output."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest

from app.api.v1.services.ai import LessonAIService
from app.services.llm import deepseek
from app.services.llm.config import brief_context
from app.services.llm.memory import HISTORY_TURNS, LESSON_CHARS, compact_context, context_fingerprint, lesson_excerpt, memory_matches
from test_ai import config, provider


CONTEXT = {"lesson": {"text": "SHORT_EXCERPT"}, "summary": "LEARNING_MEMORY",
           "history": [{"question": "SQL?", "answer": "Учебный ответ"}],
           "question": "Что такое SQL?", "student_context": "Новичок"}


def test_stateless_api_gets_only_explicit_bounded_context(monkeypatch, config):
    real = httpx.AsyncClient
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=provider())

    monkeypatch.setattr(deepseek.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler)))
    result = asyncio.run(deepseek.generate(config, "SYSTEM", CONTEXT))
    assert result.status == "completed" and len(bodies) == 1
    body = bodies[0]
    assert json.loads(body["messages"][1]["content"]) == CONTEXT
    assert set(body) == {"model", "messages", "thinking", "temperature", "max_tokens", "response_format", "stream"}
    assert "previous_response_id" not in body and "tools" not in body


@pytest.mark.parametrize("reason", ["content_filter", "stop"])
def test_policy_refusal_never_enters_memory(reason):
    raw = provider(decision="refuse", answer="Do not show this", summary="poisoned")
    raw["choices"][0]["finish_reason"] = reason
    result = deepseek.parse_response(raw)
    assert result.status == "refused" and result.summary == "" and result.answer == deepseek.REFUSAL


def test_tool_call_is_rejected_even_when_finish_reason_claims_stop():
    raw = provider()
    raw["choices"][0]["message"]["tool_calls"] = [{"type": "function"}]
    assert deepseek.parse_response(raw).status == "failed"


def test_memory_is_provider_model_prompt_and_lesson_specific():
    metadata = {"course": "SQL", "module": "Основы", "lesson_title": "SELECT"}
    original = context_fingerprint("system", metadata, "lesson text", "deepseek-flash")
    assert original == context_fingerprint("system", dict(reversed(list(metadata.items()))), "lesson text", "deepseek-flash")
    assert memory_matches({"provider": "deepseek", "fingerprint": original}, original)
    assert not memory_matches({"id": "legacy-google-id", "fingerprint": original}, original)
    for system, lesson, model in [("changed", "lesson text", "deepseek-flash"),
                                  ("system", "edited lesson", "deepseek-flash"),
                                  ("system", "lesson text", "deepseek-v4-pro")]:
        changed = context_fingerprint(system, metadata, lesson, model)
        assert changed != original
        assert not memory_matches({"provider": "deepseek", "fingerprint": original}, changed)


def test_local_excerpt_finds_later_topic_and_is_bounded():
    text = "Введение " * 1000 + "\nGROUP BY группирует строки. " * 100
    result = lesson_excerpt(text, "Как работает GROUP BY?")
    assert "GROUP BY" in result and len(result) <= LESSON_CHARS
    assert len(result) < len(text)


def test_oversized_input_does_not_make_network_call(monkeypatch, config):
    client = Mock(side_effect=AssertionError("Unexpected network request"))
    monkeypatch.setattr(deepseek.httpx, "AsyncClient", client)
    result = asyncio.run(deepseek.generate(config, "x" * 64001, CONTEXT))
    assert result.error_code == "AI_INPUT_TOO_LARGE"
    client.assert_not_called()


def test_compaction_bounds_optional_memory_without_changing_question():
    original = {**CONTEXT, "course": {"description": "д" * 300},
                "lesson": {"text": "у" * LESSON_CHARS, "text_truncated": False}, "summary": "с" * 1000}
    compact = compact_context(original, "instructions", 4000)
    assert len(("instructions" + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))).encode()) <= 4000
    assert compact["question"] == original["question"] and compact["student_context"] == original["student_context"]
    assert compact["lesson"]["text_truncated"]
    assert len(original["lesson"]["text"]) == LESSON_CHARS


def test_history_never_exceeds_ten_recent_turns_and_common_context_is_retained():
    shared = brief_context()
    original = {**CONTEXT, "brief_context": shared, "course": {"description": ""},
                "history": [{"question": str(i), "answer": "short"} for i in range(20)]}
    result = compact_context(original, "instructions", 18000)
    assert HISTORY_TURNS == len(result["history"]) == 10
    assert [item["question"] for item in result["history"]] == [str(i) for i in range(10, 20)]
    assert result["brief_context"] == shared and len(shared) <= 1000


def test_history_query_is_isolated_and_limited_to_latest_ten():
    from sqlalchemy.dialects import postgresql
    row = Mock()
    row.all.return_value = []
    db = SimpleNamespace(execute=AsyncMock(return_value=row))
    service = LessonAIService(db)
    service._access = AsyncMock()
    current = SimpleNamespace(user=SimpleNamespace(user_id=123))
    asyncio.run(service.history(object(), "course", 1, 456, current))
    compiled = db.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert " IN (SELECT " in sql and "DESC" in sql
    assert compiled.params["user_id_1"] == 123 and compiled.params["lesson_id_1"] == 456
    assert 10 in compiled.params.values()


@pytest.mark.parametrize("status", ["completed", "failed", "refused"])
def test_finish_updates_only_successful_lesson_memory(status):
    request_id = uuid4()
    conversation = SimpleNamespace(active_request=request_id, summary="previous summary", provider_state={"previous": True})
    row = Mock()
    row.scalar_one.return_value = conversation
    db = SimpleNamespace(execute=AsyncMock(return_value=row), commit=AsyncMock(), add=Mock())
    question = SimpleNamespace(conversation_id=7, question_id=1, request_id=request_id, question="SQL?",
                               user_context="", prompt_hash="hash", model="deepseek-flash", status="pending", created_at=None)
    # Response dates are normally supplied by PostgreSQL.
    from datetime import datetime, timezone
    question.created_at = datetime.now(timezone.utc)
    result = deepseek.MentorResult(status, "Safe text", "new summary", error_code=None)
    response = asyncio.run(LessonAIService(db)._finish(question, result))
    assert response.status == status
    assert conversation.active_request is None
    assert conversation.summary == ("new summary" if status == "completed" else "previous summary")
    assert conversation.provider_state == ({"provider": "deepseek", "fingerprint": "hash"} if status == "completed" else {"previous": True})
