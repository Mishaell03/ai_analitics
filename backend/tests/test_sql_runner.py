import asyncio
import json
import os
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import asyncpg
import httpx
import pytest

from app.api.v1.schemas.sandbox import ExecutionResult
from app.services.sandbox import config as config_module
from app.services.sandbox import sql_runner as module
from app.services.sandbox.config import SandboxSettings, MAX_OUTPUT_BYTES
from app.services.sandbox.runner import create_app, SandboxUnavailable
from app.services.sandbox.sql_runner import SQLRunner, validate_query


@pytest.mark.parametrize("query", [
    "SELECT * FROM customers",
    "SELECT c.city, count(*) FROM customers c JOIN orders o USING(customer_id) GROUP BY c.city",
    "WITH sales AS (SELECT * FROM order_items) SELECT sum(quantity) FROM sales",
    "SELECT row_number() OVER (ORDER BY order_id) FROM orders",
    "SELECT 'DROP TABLE customers' AS example FROM customers -- DELETE",
    "SELECT order_date::date, coalesce(status, 'unknown') FROM order_items",
])
def test_accepts_training_queries(query):
    assert validate_query(query)


@pytest.mark.parametrize("query", [
    "", "SELECT 1", "SELECT FROM", "SELECT * FROM customers; SELECT * FROM orders",
    "DELETE FROM customers", "COPY customers TO STDOUT", "SET ROLE postgres",
    "WITH gone AS (DELETE FROM customers RETURNING *) SELECT * FROM gone",
    "SELECT * INTO copy FROM customers", "SELECT * FROM customers FOR UPDATE",
    "SELECT * FROM pg_catalog.pg_authid", "SELECT * FROM information_schema.tables",
    "SELECT pg_sleep(10) FROM customers", "SELECT set_config('search_path', '', false) FROM customers",
    "SELECT pg_read_file('/etc/passwd') FROM customers", "SELECT public.lower(city) FROM customers",
    "SELECT city::regclass FROM customers", "SELECT 1 OPERATOR(public.+) 2 FROM customers",
    "WITH pg_class AS (SELECT * FROM customers) SELECT * FROM pg_class",
])
def test_rejects_non_training_queries(query):
    with pytest.raises(ValueError):
        validate_query(query)


def test_qualifies_tables_functions_and_casts():
    query = validate_query("SELECT lower(city), city::text FROM customers")
    assert "public.customers" in query
    assert "pg_catalog.lower" in query
    assert "pg_catalog.text" in query
    assert "public.pg_authid" in validate_query("SELECT * FROM pg_authid")


@pytest.fixture
def config(monkeypatch):
    monkeypatch.setenv("SANDBOX_DB_PASSWORD", "test-password")
    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    return SandboxSettings()


@pytest.fixture
def connection(monkeypatch):
    @asynccontextmanager
    async def transaction():
        yield

    async def rows():
        yield (12,)

    statement = SimpleNamespace(
        get_attributes=lambda: [SimpleNamespace(name="count")], cursor=Mock(side_effect=lambda **kw: rows()),
    )
    db = SimpleNamespace(transaction=Mock(side_effect=lambda **kw: transaction()),
                         prepare=AsyncMock(return_value=statement), terminate=Mock())
    monkeypatch.setattr(module.asyncpg, "connect", AsyncMock(return_value=db))
    return db


def test_reads_only_training_database_and_closes_connection(config, connection):
    result = asyncio.run(SQLRunner(config).execute("SELECT count(*) FROM customers"))
    assert result.success
    assert json.loads(result.stdout) == {"columns": ["count"], "rows": [[12]]}
    kwargs = module.asyncpg.connect.call_args.kwargs
    assert kwargs["database"] == "analytics_training"
    assert kwargs["user"] == "sandbox_reader"
    connection.transaction.assert_called_once_with(readonly=True)
    connection.terminate.assert_called_once()


@pytest.mark.parametrize("error,timed_out", [
    (asyncpg.UndefinedTableError('relation "missing" does not exist'), False),
    (asyncpg.QueryCanceledError("timeout"), True),
    (TimeoutError(), True),
])
def test_sql_errors_are_execution_results(config, connection, error, timed_out):
    connection.prepare.side_effect = error
    runner = SQLRunner(config)
    result = asyncio.run(runner.execute("SELECT * FROM missing"))
    assert not result.success and result.stderr
    assert result.timed_out == timed_out
    assert runner.active == 0
    connection.terminate.assert_called_once()


def test_database_unavailable_is_not_a_student_error(config, monkeypatch):
    monkeypatch.setattr(module.asyncpg, "connect", AsyncMock(side_effect=OSError()))
    runner = SQLRunner(config)
    with pytest.raises(SandboxUnavailable):
        asyncio.run(runner.execute("SELECT * FROM customers"))
    assert runner.active == 0


def test_output_is_bounded_and_stays_valid_json(config, connection):
    async def rows():
        yield ("x" * MAX_OUTPUT_BYTES,)

    connection.prepare.return_value.cursor.side_effect = lambda **kw: rows()
    result = asyncio.run(SQLRunner(config).execute("SELECT city FROM customers"))
    assert result.output_limited and not result.success
    assert len(result.stdout.encode()) <= MAX_OUTPUT_BYTES
    assert json.loads(result.stdout)["rows"] == []


def test_cancellation_releases_connection(config, connection):
    connection.prepare.side_effect = asyncio.CancelledError()
    runner = SQLRunner(config)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(runner.execute("SELECT * FROM customers"))
    connection.terminate.assert_called_once()
    assert runner.active == 0


@pytest.mark.parametrize("language", ["sql", "python"])
def test_runner_routes_language(config, language):
    app = create_app(config)
    result = ExecutionResult(stdout="ok", stderr="", exit_code=0, timed_out=False, duration=0.1)
    app.state.sql_runner.execute = AsyncMock(return_value=result)
    app.state.runner.execute = AsyncMock(return_value=result)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/execute", json={
                "code": "SELECT * FROM customers" if language == "sql" else 'print("hello world")',
                "language": language, "profile": "light",
            }, headers={"Authorization": "Bearer " + config.token})
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert app.state.sql_runner.execute.await_count == (language == "sql")
        assert app.state.runner.execute.await_count == (language == "python")

    asyncio.run(scenario())


def test_common_env_fallback_and_process_override(monkeypatch):
    monkeypatch.delenv("SANDBOX_RUNNER_TOKEN", raising=False)
    monkeypatch.setattr(config_module, "dotenv_values", lambda path: {"SANDBOX_RUNNER_TOKEN": "t" * 32})
    assert SandboxSettings().token == "t" * 32
    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "override")
    assert SandboxSettings().token == "override"


def test_sql_lifespan_does_not_require_docker(config):
    app = create_app(config)
    app.state.runner.recover = AsyncMock(side_effect=SandboxUnavailable("Docker unavailable"))
    app.state.runner.watch = AsyncMock()

    async def scenario():
        async with app.router.lifespan_context(app):
            assert not app.state.runner.healthy
            assert app.state.sql_runner is not None
    asyncio.run(scenario())


@pytest.mark.skipif(os.getenv("SANDBOX_SQL_TESTS") != "1", reason="requires analytics_training")
def test_real_training_database():
    async def scenario():
        runner = SQLRunner(SandboxSettings())
        result = await runner.execute("SELECT count(*) FROM customers")
        assert result.success, result.stderr
        assert json.loads(result.stdout)["rows"][0][0] >= 0
        result = await runner.execute("SELECT missing_column FROM customers")
        assert not result.success and result.stderr
        config = SandboxSettings()
        app = create_app(config)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/execute", json={
                "code": "SELECT count(*) FROM customers", "language": "sql", "profile": "light",
            }, headers={"Authorization": "Bearer " + config.token})
        assert response.status_code == 200
        assert response.json()["success"] is True
    asyncio.run(scenario())
