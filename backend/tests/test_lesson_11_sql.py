"""Offline SQL checks: AST validation, canonical data and expected lesson results.

SQLite checks query logic, not PostgreSQL connection, ACL or wire serialization.
"""

import ast
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3

import pytest

from app.api.v1.schemas.sandbox import ExecutionResult
from app.api.v1.services.sandbox import SandboxService
from app.core.markdown import MarkdownParser
from app.services.sandbox.sql_runner import validate_query


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "infra/postgres/core_db/seeds/R__lesson_11_answers.sql"
CONTENT = ROOT / "infra/minio/seeds/course-content/1/4/11.md"


def references():
    return re.findall(
        r"\('(lesson_11_sql_\w+)', \$sql\$(.*?)\$sql\$, (true|false),\s*\$result\$(.*?)\$result\$\)",
        SEED.read_text(), re.S,
    )


def canonical_rows():
    seed = (ROOT / "infra/postgres/analytics_training/seeds/R__severny_svet.sql").read_text()
    values = seed.split(") VALUES", 1)[1].split("ON CONFLICT", 1)[0].strip()
    return ast.literal_eval("[" + values + "]")


def test_lesson_11_blocks_and_test_choices():
    source = CONTENT.read_text()
    parsed = MarkdownParser().parse(source)
    assert {b.data["exercise_id"] for b in parsed.custom_blocks if b.type == "code"} == {
        row[0] for row in references()
    }
    assert len(references()) == 7
    answers = dict(re.findall(r"\(11, '([^']+)', \$answer\$(.*?)\$answer\$\)", SEED.read_text()))
    tests = re.findall(r":::test\s*\nid: (\w+)\n(.*?)\n:::", source, re.S)
    assert len(tests) == 6
    for (exercise_id, body), number in zip(tests, [2, 3, 4, 1, 2, 3]):
        options = re.findall(r"^- \( \) (.*)$", body, re.M)
        assert json.loads(answers[exercise_id])["correct"] == [options[number - 1]]
    assert "МЕСТО ДЛЯ" not in source


def test_lesson_11_queries_against_canonical_data():
    def normalize(value):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return value

    rows = canonical_rows()
    assert len(rows) == 10
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE order_items (line_item_id, order_id, order_date, customer_id, product, category, quantity, unit_price, status)")
        db.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?,?,?,?)", rows)
        for exercise_id, query, ordered, result in references():
            validate_query(query)
            actual = [[normalize(v) for v in row] for row in db.execute(query)]
            expected = [[normalize(v) for v in row] for row in json.loads(result)["rows"]]
            if ordered == "false":
                actual, expected = sorted(actual), sorted(expected)
            assert actual == expected, exercise_id
        assert db.execute("SELECT COUNT(DISTINCT order_id) FROM order_items").fetchone()[0] == 8


@pytest.mark.parametrize("ordered,expected", [(False, True), (True, False)])
def test_unordered_sql_grading(ordered, expected):
    target = {"columns": ["id"], "rows": [[1], [2], [2]]}
    actual = {"columns": ["id"], "rows": [[2], [1], [2]]}
    reference = ExecutionResult(stdout=json.dumps(target), stderr="", exit_code=0, timed_out=False, duration=0)
    result = reference.model_copy(update={"stdout": json.dumps(actual)})
    answer = json.dumps({"type": "code", "language": "sql", "ordered": ordered, "execution": reference.model_dump()})
    assert SandboxService.grade(result, answer, "sql") is expected
    missing = result.model_copy(update={"stdout": json.dumps({"columns": ["id"], "rows": [[1], [2]]})})
    assert SandboxService.grade(missing, answer, "sql") is False
