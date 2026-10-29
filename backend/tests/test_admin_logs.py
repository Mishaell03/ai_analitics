import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.api.v1.routes.admin_logs import router
from app.api.v1.schemas.admin_logs import AILogFilters, SystemLogFilters
from app.api.v1.services.admin_logs import AdminLogsService
from app.core.database import get_db
from app.core.session import get_current_admin
from app.core import exception_handlers


def test_admin_log_indexes_do_not_conflict_with_previous_migrations():
    migrations = Path(__file__).resolve().parents[1] / "infra/postgres/core_db/migrations"
    pattern = re.compile(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.IGNORECASE)
    previous = {
        name.lower()
        for path in migrations.glob("V*.sql")
        if int(path.name.split("__", 1)[0][1:]) < 11
        for name in pattern.findall(path.read_text())
    }
    added = [name.lower() for name in pattern.findall((migrations / "V11__admin_logs.sql").read_text())]
    assert len(added) == len(set(added))
    assert not previous.intersection(added)


class FakeResult:
    def __init__(self, count=None, rows=None):
        self.count = count
        self.rows = rows or []

    def scalar_one(self):
        return self.count

    def mappings(self):
        return self.rows


class FakeDB:
    def __init__(self, rows=None):
        self.queries = []
        self.rows = rows or []

    async def execute(self, query):
        self.queries.append(query)
        return FakeResult(count=len(self.rows)) if len(self.queries) == 1 else FakeResult(rows=self.rows)


def compile_query(query):
    return query.compile(dialect=postgresql.dialect())


def test_system_filters_and_pagination_are_applied_in_database():
    db = FakeDB()
    result = asyncio.run(AdminLogsService(db).get_system_logs(SystemLogFilters(
        page=2, page_size=10, user="test%_", user_id=7, session_id=42,
        source="backend", status="server_error", status_code=503, code="AI_UNAVAILABLE",
        date_from="2026-10-01", date_to="2026-10-02",
    )))
    compiled = compile_query(db.queries[1])
    sql = str(compiled)
    params = compiled.params.values()
    assert "UNION ALL" in sql
    assert "LEFT OUTER JOIN users_sessions" in sql
    assert "LIMIT" in sql and "OFFSET" in sql
    assert "ORDER BY" in sql
    for value in (7, 42, 500, 599, 503, "AI_UNAVAILABLE", "backend", 10):
        assert value in params
    assert datetime(2026, 10, 1, tzinfo=timezone.utc) in params
    assert datetime(2026, 10, 2, 23, 59, 59, 999999, tzinfo=timezone.utc) in params
    assert "test/%/_" in params  # LIKE-метасимволы не меняют смысл поиска
    assert result["total_pages"] == 1
    assert result["items"] == []
    assert "request_body" not in sql and "error_message" not in sql


def test_ai_logs_keep_pending_questions_and_do_not_expose_internal_context():
    db = FakeDB()
    asyncio.run(AdminLogsService(db).get_ai_logs(AILogFilters(user="123", status="pending")))
    compiled = compile_query(db.queries[1])
    sql = str(compiled)
    assert "LEFT OUTER JOIN ai_answers" in sql
    assert "pending" in compiled.params.values()
    assert 123 in compiled.params.values()
    for field in ("provider_response", "provider_state", "context_snapshot", "prompt_hash", "user_context"):
        assert field not in sql


@pytest.mark.parametrize("kwargs", [
    {"page": 0}, {"page_size": 101}, {"session_id": 0}, {"status_code": 600},
    {"date_from": "2026-10-02", "date_to": "2026-10-01"}, {"status": "unknown"},
])
def test_invalid_filters_are_rejected(kwargs):
    with pytest.raises(ValidationError):
        SystemLogFilters(**kwargs)


def make_app(admin=True):
    app = FastAPI()
    app.include_router(router)
    db = FakeDB()

    async def current_admin():
        if not admin:
            raise HTTPException(status_code=403)
        return object()

    app.dependency_overrides[get_current_admin] = current_admin
    app.dependency_overrides[get_db] = lambda: db
    return app, db


@pytest.mark.parametrize("path", ["/admin/logs", "/admin/logs/ai"])
def test_admin_dependency_protects_both_log_endpoints(path):
    app, db = make_app(admin=False)
    with TestClient(app) as client:
        assert client.get(path).status_code == 403
    assert not db.queries


@pytest.mark.parametrize("path", ["/admin/logs", "/admin/logs/ai"])
def test_logs_are_paginated_and_not_cached(path):
    app, _ = make_app()
    with TestClient(app) as client:
        response = client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"page": 1, "page_size": 20, "total": 0, "total_pages": 1, "items": []}


def test_bad_date_range_returns_422():
    app, db = make_app()
    with TestClient(app) as client:
        response = client.get("/admin/logs?date_from=2026-10-02&date_to=2026-10-01")
    assert response.status_code == 422
    assert not db.queries


@pytest.mark.parametrize("detail, expected", [
    ({"code": "AI_UNAVAILABLE", "message": "Unavailable"}, "AI_UNAVAILABLE"),
    ("Unavailable", "HTTP_503"),
])
def test_http_error_code_is_forwarded_to_persistent_logger(monkeypatch, detail, expected):
    records = []

    async def capture(**kwargs):
        records.append(kwargs)

    monkeypatch.setattr(exception_handlers, "backend_error_logs", capture)
    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})
    response = asyncio.run(exception_handlers.server_error_handler(request, HTTPException(503, detail)))
    assert response.status_code == 503
    assert records[0]["error_code"] == expected
