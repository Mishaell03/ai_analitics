"""Материалы урока 12: данные seeds, SQL, ключи тестов и безопасная привязка.

SQLite проверяет логику offline. Опциональная проверка PostgreSQL выполняет
только SELECT с VALUES-CTE из seeds, не создаёт таблиц и не изменяет данные.
"""

import asyncio
import json
import os
from pathlib import Path
import re
import sqlite3

import pytest

from app.core.markdown import MarkdownParser
from app.services.sandbox.sql_runner import validate_query
from scripts.prepare_lesson_12 import prepare_content

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "infra/minio/seeds/course-content/1/4/12.md"
MANIFEST = json.loads((ROOT / "docs/lesson-12/solutions.json").read_text())
TRAINING = ROOT / "infra/postgres/analytics_training"


def sample_database():
    db = sqlite3.connect(":memory:")
    for path in sorted((TRAINING / "migrations").glob("V*.sql")):
        # SQLite main schema corresponds to PostgreSQL public in this fixture.
        db.executescript(path.read_text().replace("public.", ""))
    for path in sorted((TRAINING / "seeds").glob("R__*.sql")):
        db.executescript(path.read_text().replace("public.", ""))
    return db


def postgres_fixture_cte():
    seed = (TRAINING / "seeds/R__retail_sales.sql").read_text()
    tables = []
    for table in ("customers", "retail_order_items"):
        match = re.search(rf"INSERT INTO {table}\s*\((.*?)\)\s*VALUES\s*(.*?)\s*ON CONFLICT", seed, re.S)
        assert match, table
        tables.append(f"{table} ({match[1]}) AS (VALUES {match[2]})")
    return "WITH " + ",\n".join(tables) + "\n"


def fake_references():
    # Только тестовые записи. Это НЕ ID в реальной БД и не публикуемый Markdown.
    return [{"answer_id": index, "exercise_id": f"test_fixture_{index}",
             "answer": json.dumps({"type": "code", "language": "sql", "check_mode": "self_review", "value": item["code"]})}
            for index, item in enumerate(MANIFEST["assignments"], 1)]


def test_unlinked_materials_are_explicitly_draft():
    assert MANIFEST["status"] == "draft_unlinked"
    assert MANIFEST["lesson_id"] is None
    assert all(item["exercise_id"] is None and item["answer_id"] is None for item in MANIFEST["assignments"])
    blocks = MarkdownParser().parse(CONTENT.read_text()).custom_blocks
    assert len([b for b in blocks if b.type == "code"]) == 3
    assert CONTENT.read_text().count("id: none") == 3


def test_all_three_editors_bind_to_only_their_own_reference():
    refs = fake_references()
    bound = prepare_content(CONTENT.read_text(), MANIFEST["assignments"], refs)
    blocks = [b for b in MarkdownParser().parse(bound).custom_blocks if b.type == "code"]
    assert [b.data["exercise_id"] for b in blocks] == [r["exercise_id"] for r in refs]
    assert all(b.data["body"] == "" and b.data["language"] == "sql" for b in blocks)
    assert all(not b.data.get("practice") for b in blocks)
    for item in MANIFEST["assignments"]:
        assert item["code"] not in bound


@pytest.mark.parametrize("case", ["swapped", "duplicate", "missing", "none", "graded"])
def test_invalid_reference_mapping_rejected(case):
    refs = fake_references()
    if case == "swapped":
        refs[0], refs[1] = refs[1], refs[0]
    elif case == "duplicate":
        refs[1]["exercise_id"] = refs[0]["exercise_id"]
    elif case == "missing":
        refs.pop()
    elif case == "none":
        refs[0]["exercise_id"] = "none"
    else:
        answer = json.loads(refs[0]["answer"])
        answer["check_mode"] = "graded"
        refs[0]["answer"] = json.dumps(answer)
    with pytest.raises(ValueError):
        prepare_content(CONTENT.read_text(), MANIFEST["assignments"], refs)


def test_test_ids_and_answer_key_match_all_six_questions():
    source = CONTENT.read_text()
    tests = re.findall(r":::test\s*\nid: (\w+)\n(.*?)\n:::", source, re.S)
    assert len(tests) == 6
    assert [item["option"] for item in MANIFEST["tests"]] == [2, 3, 1, 4, 1, 3]
    for (exercise_id, body), answer in zip(tests, MANIFEST["tests"]):
        assert exercise_id == answer["exercise_id"]
        options = re.findall(r"^- \( \) (.*)$", body, re.M)
        assert len(options) == 4
        assert answer["correct"] == [options[answer["option"] - 1]]
        assert answer["type"] == "single_choice"
    assert not re.search(r"\([xXхХ]\)|\[[xXхХ]\]", source)


def test_seed_control_totals_and_unrelated_legacy_customers():
    with sample_database() as db:
        assert db.execute("SELECT COUNT(*) FROM retail_order_items").fetchone() == (36,)
        assert db.execute("SELECT COUNT(*) FROM retail_order_items WHERE status='cancelled'").fetchone() == (4,)
        assert db.execute("SELECT COUNT(*),COUNT(DISTINCT order_id),SUM(quantity),SUM(quantity*unit_price) FROM retail_order_items WHERE status='completed'").fetchone() == (32, 17, 62, 302780)
        assert db.execute("SELECT SUM(r.quantity*r.unit_price) FROM retail_order_items r JOIN customers c ON c.customer_id=r.customer_id WHERE r.status='completed' AND c.city IS NULL").fetchone() == (460,)
        assert db.execute("SELECT COUNT(*) FROM order_items o JOIN customers c ON c.customer_id=o.customer_id").fetchone() == (0,)


def test_all_reference_queries_and_student_examples_run_against_seeds():
    with sample_database() as db:
        for assignment in MANIFEST["assignments"]:
            validate_query(assignment["code"])
            result = db.execute(assignment["code"])
            assert [c[0] for c in result.description] == assignment["expected_columns"]
            assert [list(row) for row in result] == assignment["expected_rows"]
        examples = re.findall(r"```sql\n(.*?)\n```", CONTENT.read_text(), re.S)
        assert len(examples) == 7
        for query in examples:
            validate_query(query)
            rows = db.execute(query).fetchall()
            assert rows
        assert db.execute(examples[-1]).fetchone() == (12, 123030)


@pytest.mark.parametrize("sql", [
    "DELETE FROM retail_order_items", "SELECT * INTO new_sales FROM retail_order_items",
    "SELECT * FROM customers FOR UPDATE", "SELECT * FROM pg_catalog.pg_authid",
    "SELECT pg_read_file('/etc/passwd') FROM customers", "SELECT * FROM customers; DROP TABLE customers",
])
def test_read_only_sandbox_restrictions_remain(sql):
    with pytest.raises(ValueError):
        validate_query(sql)


@pytest.mark.parametrize("use_seed_fixture", [True, False])
def test_native_postgresql_reference_queries_and_examples(use_seed_fixture):
    flag = "LESSON12_POSTGRES_TESTS" if use_seed_fixture else "LESSON12_LIVE_DATA_TESTS"
    if os.getenv(flag) != "1":
        pytest.skip(f"opt-in {flag}: read-only PostgreSQL checks")
    import asyncpg
    from sqlalchemy.engine import make_url
    from app.core.config import settings

    async def scenario():
        url = make_url(settings.database_url)
        conn = await asyncpg.connect(host=url.host, port=url.port or 5432, user=url.username,
                                     password=url.password, database="analytics_training", timeout=5)
        try:
            async with conn.transaction(readonly=True):
                assert await conn.fetchval("SHOW transaction_read_only") == "on"
                prefix = postgres_fixture_cte() if use_seed_fixture else ""
                totals = await conn.fetchrow(prefix + """
                    SELECT count(*), count(*) FILTER (WHERE status='completed'),
                        count(*) FILTER (WHERE status='cancelled'), count(DISTINCT order_id),
                        count(DISTINCT order_id) FILTER (WHERE status='completed'),
                        sum(quantity) FILTER (WHERE status='completed'),
                        sum(quantity*unit_price) FILTER (WHERE status='completed')
                    FROM retail_order_items
                """)
                assert tuple(totals) == (36, 32, 4, 20, 17, 62, 302780)
                for assignment in MANIFEST["assignments"]:
                    rows = await conn.fetch(prefix + assignment["code"])
                    assert list(rows[0].keys()) == assignment["expected_columns"]
                    assert [list(r.values()) for r in rows] == assignment["expected_rows"]
                for query in re.findall(r"```sql\n(.*?)\n```", CONTENT.read_text(), re.S):
                    assert await conn.fetch(prefix + query)
        finally:
            await conn.close()

    asyncio.run(scenario())
