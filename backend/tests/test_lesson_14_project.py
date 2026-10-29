"""Lesson 14 expert programs, actual retail rows and output checks, offline."""

import ast
import csv
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from app.api.v1.schemas.sandbox import ExecutionResult
from app.core.markdown import MarkdownParser
from app.services.sandbox.plots import python_with_plots, extract_plot_output
from app.services.sandbox.project_grading import grade_project

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "infra/postgres/core_db/seeds/R__lesson_14_answers.sql"
CONTENT = ROOT / "infra/minio/seeds/course-content/1/5/14.md"


def dataset():
    return re.search(r"\$csv\$(.*?)\$csv\$", SEED.read_text(), re.S)[1]


def references():
    seed = SEED.read_text()
    prefix = re.search(r"\$prefix\$(.*?)\$prefix\$", seed, re.S)[1]
    return {key: prefix + dataset() + '"""\n\n' + body for key, body in re.findall(
        r"\('(lesson_14_python_\d+)', \$python\$(.*?)\$python\$\)", seed, re.S,
    )}


def test_project_csv_is_identical_to_real_retail_rows_and_markdown():
    source = (ROOT / "infra/postgres/analytics_training/seeds/R__retail_sales.sql").read_text()
    raw_values = source.split("INSERT INTO retail_order_items", 1)[1].split(") VALUES", 1)[1].split("ON CONFLICT", 1)[0]
    rows = ast.literal_eval("[" + raw_values.strip() + "]")
    loaded = list(csv.reader(io.StringIO(dataset())))[1:]
    assert len(loaded) == len(rows) == 36
    for actual, expected in zip(loaded, rows):
        assert actual[:1] == [str(expected[0])]
        assert actual[1:7] == [str(value) for value in expected[1:7]]
        assert float(actual[7]) == expected[7]
        assert actual[8] == expected[8]
    md_csv = re.search(r"```csv\n(.*?)\n```", CONTENT.read_text(), re.S)[1]
    assert list(csv.reader(io.StringIO(md_csv))) == list(csv.reader(io.StringIO(dataset())))


def test_project_ids_and_test_choices_match_seeds():
    source, seed = CONTENT.read_text(), SEED.read_text()
    parsed = MarkdownParser().parse(source)
    assert len(references()) == 3
    assert {b.data["exercise_id"] for b in parsed.custom_blocks if b.type == "code"} == set(references())
    assert "id: none" not in source
    answers = dict(re.findall(r"\(14, '(lesson_14_test_\d+)', \$answer\$(.*?)\$answer\$\)", seed))
    blocks = re.findall(r":::test\nid: (lesson_14_test_\d+)\n(.*?)\n:::", source, re.S)
    assert len(blocks) == 6
    for (key, body), number in zip(blocks, [3, 1, 4, 2, 3, 2]):
        assert json.loads(answers[key])["correct"] == [re.findall(r"^- \( \) (.*)$", body, re.M)[number - 1]]


def test_module_5_and_lessons_are_inserted_once_with_correct_positions():
    from pglast import ast as sql_ast, parse_sql

    inserts = {"lessons": [], "course_modules": []}
    rows_by_id = {}
    seed = (ROOT / "infra/postgres/core_db/seeds/R__courses.sql").read_text()
    for raw in parse_sql(seed):
        statement = raw.stmt
        if not isinstance(statement, sql_ast.InsertStmt) or statement.relation.relname not in inserts:
            continue
        table = statement.relation.relname
        columns = [column.name for column in statement.cols]
        for row in statement.selectStmt.valuesLists:
            identity = row[0].val.ival
            inserts[table].append(identity)
            rows_by_id[table, identity] = dict(zip(columns, row))
    assert all(len(ids) == len(set(ids)) for ids in inserts.values())
    module = rows_by_id["course_modules", 5]
    assert module["course_id"].val.ival == 1
    assert module["position"].val.ival == 5
    for lesson_id, position in [(13, 1), (14, 2)]:
        row = rows_by_id["lessons", lesson_id]
        assert row["module_id"].val.ival == 5
        assert row["position"].val.ival == position
        assert row["is_published"].val.boolval is True


@pytest.mark.parametrize("exercise_id", [f"lesson_14_python_{n:02d}" for n in range(1, 4)])
def test_expert_program_executes_independently_and_passes_checks(exercise_id):
    pytest.importorskip("pandas")
    pytest.importorskip("matplotlib")
    code = references()[exercise_id]
    assert len(code) <= 8000
    result = subprocess.run([sys.executable, "-I", "-c", python_with_plots(code)],
        capture_output=True, timeout=15, env={**os.environ, "MPLCONFIGDIR": "/tmp/opencode/mpl-test"})
    assert result.returncode == 0, result.stderr.decode()
    text, plots, limited, chart_data = extract_plot_output(result.stdout)
    execution = ExecutionResult(stdout=text.decode(), stderr=result.stderr.decode(), plots=plots,
        chart_data=chart_data, exit_code=result.returncode, timed_out=False, duration=0, output_limited=limited)
    assert grade_project(execution, exercise_id) == (True, None)
    assert len(plots) == (0 if exercise_id.endswith("01") else 1)
    assert "302780" in execution.stdout
    # Missing output must not become eligible merely because a plot was drawn.
    assert grade_project(execution.model_copy(update={"stdout": ""}), exercise_id)[0] is False


@pytest.mark.parametrize("exercise_id", [f"lesson_14_python_{n:02d}" for n in range(1, 4)])
def test_empty_success_does_not_unlock_project_expert(exercise_id):
    blank = ExecutionResult(stdout="\n", stderr="", exit_code=0, timed_out=False, duration=0)
    assert grade_project(blank, exercise_id)[0] is False
