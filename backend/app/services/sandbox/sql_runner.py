"""Учебные SELECT-запросы: отдельное подключение только к analytics_training."""

import asyncio
import json
import time

import asyncpg
from pglast import ast, parse_sql
from pglast.parser import ParseError, parse_sql_json
from pglast.stream import RawStream
from pglast.visitors import Visitor

from app.api.v1.schemas.sandbox import ExecutionResult
from app.services.sandbox.config import MAX_OUTPUT_BYTES, SandboxSettings


FUNCTIONS = frozenset({
    "count", "sum", "avg", "min", "max", "abs", "round", "ceil", "ceiling", "floor",
    "sqrt", "power", "mod", "sign", "trunc", "length", "char_length", "lower", "upper",
    "substring", "substr", "replace", "trim", "btrim", "ltrim", "rtrim", "concat",
    "concat_ws", "left", "right", "strpos", "split_part", "date_part", "date_trunc",
    "extract", "to_char", "to_date", "to_timestamp", "age", "now", "current_date",
    "row_number", "rank", "dense_rank", "ntile", "lag", "lead", "first_value",
    "last_value", "nth_value", "string_agg", "array_agg", "bool_and", "bool_or",
    "every", "stddev", "stddev_pop", "stddev_samp", "variance", "var_pop", "var_samp",
})
TYPES = frozenset({
    "int2", "int4", "int8", "integer", "smallint", "bigint", "numeric", "decimal",
    "float4", "float8", "real", "double precision", "text", "varchar", "bpchar",
    "bool", "boolean", "date", "time", "timetz", "timestamp", "timestamptz",
    "interval", "json", "jsonb", "uuid",
})


def validate_query(code: str) -> str:
    """Проверяем AST, а не ключевые слова внутри строк/комментариев."""
    try:
        statements = json.loads(parse_sql_json(code))["stmts"]
    except ParseError as exc:
        raise ValueError(str(exc)) from None
    if len(statements) != 1 or "SelectStmt" not in statements[0]["stmt"]:
        raise ValueError("Разрешён один SELECT-запрос к учебным таблицам.")
    tables = []
    ctes = set()

    def names(items):
        return [item.get("String", {}).get("sval", "") for item in items]

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for kind, node in value.items():
                if kind.endswith("Stmt") and kind != "SelectStmt":
                    raise ValueError("Изменение данных и служебные SQL-команды запрещены.")
                if kind == "SelectStmt" and (node.get("intoClause") or node.get("lockingClause")):
                    raise ValueError("SELECT INTO и блокировки строк запрещены.")
                if kind == "CommonTableExpr":
                    if node["ctename"].lower().startswith("pg_"):
                        raise ValueError("Имена pg_* зарезервированы системой.")
                    ctes.add(node["ctename"])
                if kind == "RangeVar":
                    if node.get("catalogname") or node.get("schemaname") not in (None, "public"):
                        raise ValueError("Доступны только таблицы public в analytics_training.")
                    tables.append(node)
                if kind == "FuncCall":
                    parts = names(node["funcname"])
                    if (len(parts) not in (1, 2) or parts[-1] not in FUNCTIONS
                            or (len(parts) == 2 and parts[0] != "pg_catalog")):
                        raise ValueError("Эта функция недоступна в учебной среде.")
                if kind in {"TypeName", "typeName"}:
                    parts = names(node.get("names", []))
                    if (not parts or parts[-1] not in TYPES or len(parts) > 2
                            or (len(parts) == 2 and parts[0] != "pg_catalog")):
                        raise ValueError("Этот тип данных недоступен в учебной среде.")
                if kind == "A_Expr" and len(node.get("name", [])) > 1:
                    raise ValueError("Пользовательские операторы запрещены.")
                walk(node)

    walk(statements[0]["stmt"])
    if not any(table.get("schemaname") == "public" or table["relname"] not in ctes for table in tables):
        raise ValueError("Укажите учебную таблицу в FROM или JOIN.")

    class Qualify(Visitor):
        def visit_RangeVar(self, ancestors, node):
            if node.schemaname is None and node.relname not in ctes:
                node.schemaname = "public"

        def visit_FuncCall(self, ancestors, node):
            node.funcname = (ast.String(sval="pg_catalog"), node.funcname[-1])

        def visit_TypeName(self, ancestors, node):
            node.names = (ast.String(sval="pg_catalog"), node.names[-1])

    tree = parse_sql(code)
    Qualify()(tree)
    return RawStream()(tree)


class SQLRunner:
    def __init__(self, config: SandboxSettings):
        self.config = config
        self.active = 0

    async def execute(self, code: str) -> ExecutionResult:
        # Импорт здесь исключает цикл при создании приложения runner.
        from app.services.sandbox.runner import SandboxBusy, SandboxUnavailable

        started = time.monotonic()
        result = dict(stdout="", stderr="", exit_code=0, timed_out=False)
        try:
            code = validate_query(code)
        except ValueError as exc:
            return ExecutionResult(**{**result, "stderr": str(exc), "exit_code": 1}, duration=0)
        if not self.config.sql_password:
            raise SandboxUnavailable("SANDBOX_DB_PASSWORD is missing")
        if self.active >= self.config.concurrency:
            raise SandboxBusy()
        self.active += 1
        connection = None
        try:
            try:
                connection = await asyncpg.connect(
                    host=self.config.sql_host, port=self.config.sql_port,
                    user="sandbox_reader", password=self.config.sql_password,
                    database="analytics_training", timeout=5, command_timeout=5,
                    server_settings={
                        "application_name": "analytics_sql_sandbox",
                        "search_path": "pg_catalog, public",
                        "statement_timeout": "5000", "lock_timeout": "1000",
                        "idle_in_transaction_session_timeout": "10000",
                        "default_transaction_read_only": "on", "work_mem": "4MB",
                    },
                )
            except (OSError, asyncpg.PostgresError, TimeoutError):
                raise SandboxUnavailable("Training database unavailable") from None
            try:
                async with asyncio.timeout(6), connection.transaction(readonly=True):
                    statement = await connection.prepare(code)
                    columns = [attribute.name for attribute in statement.get_attributes()]
                    prefix = json.dumps({"columns": columns}, ensure_ascii=False)[:-1] + ', "rows": ['
                    chunks = [prefix]
                    size = len(prefix.encode()) + 2
                    count = 0
                    if size > MAX_OUTPUT_BYTES:
                        result.update(stdout='{"columns": [], "rows": []}', output_limited=True)
                    else:
                        async for row in statement.cursor(prefetch=1):
                            chunk = ("," if count else "") + json.dumps(list(row), ensure_ascii=False, default=str)
                            length = len(chunk.encode())
                            if count >= 1000 or size + length > MAX_OUTPUT_BYTES:
                                result["output_limited"] = True
                                break
                            chunks.append(chunk)
                            size += length
                            count += 1
                        result["stdout"] = "".join(chunks) + "]}"
            except (TimeoutError, asyncpg.QueryCanceledError):
                result.update(exit_code=1, timed_out=True, stderr="Превышено время выполнения SQL (5 секунд).")
            except asyncpg.PostgresError as exc:
                result.update(exit_code=1, stderr=str(exc)[:4096])
            return ExecutionResult(**result, duration=round(time.monotonic() - started, 3))
        finally:
            if connection is not None:
                # Выделенное соединение не возвращается в пул; закрытие также отменяет запрос.
                connection.terminate()
            self.active -= 1
