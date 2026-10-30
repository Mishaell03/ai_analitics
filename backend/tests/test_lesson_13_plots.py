"""Actual lesson data and PNG capture, without Docker, DB or running servers."""

import ast
import asyncio
import base64
import csv
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import AsyncMock

import pytest

from app.api.v1.schemas.sandbox import ExecutionResult
from app.core.markdown import MarkdownParser
from app.services.sandbox.plots import MAX_PLOTS, PREFIX, extract_plots, extract_plot_output, python_with_plots
from app.services.sandbox.chart_grading import grade_chart

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "infra/minio/seeds/course-content/1/5/13.md"
SEED = ROOT / "infra/postgres/core_db/seeds/R__lesson_13_answers.sql"


def references():
    return dict(re.findall(r"\('(lesson_13_python_\d+)', \$python\$(.*?)\$python\$\)", SEED.read_text(), re.S))


def retail_rows():
    source = (ROOT / "infra/postgres/analytics_training/seeds/R__retail_sales.sql").read_text()
    values = source.split("INSERT INTO retail_order_items", 1)[1].split(") VALUES", 1)[1].split("ON CONFLICT", 1)[0]
    return ast.literal_eval("[" + values.strip() + "]")


def csv_blocks(source):
    return re.findall(r"```csv\n(.*?)\n```", source, re.S)


def test_lesson_13_real_rows_and_summaries_match_seeds():
    source = CONTENT.read_text()
    blocks = csv_blocks(source)
    raw = next(block for block in blocks if block.startswith("line_item_id,"))
    projection = [(r[0], r[2], r[5], r[6], Decimal(str(r[7])), r[8]) for r in retail_rows()]
    loaded = [(int(r["line_item_id"]), r["order_date"], r["category"], int(r["quantity"]),
               Decimal(r["unit_price"]), r["status"]) for r in csv.DictReader(io.StringIO(raw))]
    assert loaded == projection
    assert len(loaded) == 36
    completed = [row for row in loaded if row[-1] == "completed"]
    assert len(completed) == 32
    assert sum(row[3] for row in completed) == 62
    assert sum(row[3] * row[4] for row in completed) == 302780
    assert next(row for row in completed if row[0] == 28)[4] == 0
    categories = {}
    months = {}
    for _, day, category, quantity, price, _ in completed:
        categories[category] = categories.get(category, Decimal(0)) + quantity * price
        months[day[:7]] = months.get(day[:7], Decimal(0)) + quantity * price
    category_csv = next(b for b in blocks if b.startswith("category,"))
    month_csv = next(b for b in blocks if b.startswith("month,"))
    assert {r["category"]: Decimal(r["revenue"]) for r in csv.DictReader(io.StringIO(category_csv))} == categories
    assert {r["month"]: Decimal(r["revenue"]) for r in csv.DictReader(io.StringIO(month_csv))} == months
    expert_csv = re.search(r'csv_text = """(.*?)"""', references()["lesson_13_python_03"], re.S)[1]
    assert list(csv.DictReader(io.StringIO(expert_csv))) == list(csv.DictReader(io.StringIO(raw)))


def test_lesson_13_exercise_links_and_test_answers():
    source = CONTENT.read_text()
    parsed = MarkdownParser().parse(source)
    assert len(references()) == 3
    assert {b.data["exercise_id"] for b in parsed.custom_blocks if b.type == "code"} == set(references())
    assert "id: none" not in source
    seed = SEED.read_text()
    answers = dict(re.findall(r"\(13, '(lesson_13_test_\d+)', \$answer\$(.*?)\$answer\$\)", seed))
    blocks = re.findall(r":::test\nid: (lesson_13_test_\d+)\n(.*?)\n:::", source, re.S)
    assert len(blocks) == 6
    for (key, body), number in zip(blocks, [2, 3, 1, 4, 2, 3]):
        assert json.loads(answers[key])["correct"] == [re.findall(r"^- \( \) (.*)$", body, re.M)[number - 1]]


def run_capture(code):
    pytest.importorskip("pandas")
    pytest.importorskip("matplotlib")
    result = subprocess.run(
        [sys.executable, "-I", "-c", python_with_plots(code)], capture_output=True,
        env={**os.environ, "MPLCONFIGDIR": "/tmp/opencode/mpl-test", "OPENBLAS_NUM_THREADS": "1"}, timeout=15,
    )
    return result, extract_plots(result.stdout)


@pytest.mark.parametrize("exercise_id", ["lesson_13_python_01", "lesson_13_python_02", "lesson_13_python_03"])
def test_each_lesson_13_reference_really_emits_a_png(exercise_id):
    code = references()[exercise_id]
    result, (text, plots, limited) = run_capture(code)
    assert result.returncode == 0, result.stderr.decode()
    assert len(plots) == 1 and not limited
    assert b"302780" in text
    if exercise_id.endswith("02"):
        assert b"-74640" in text and b"62210" in text
    if exercise_id.endswith("03"):
        assert "Завершённых позиций: 32" in text.decode()
        assert "Итоги совпадают: True" in text.decode()
    execution = ExecutionResult(stdout=text.decode(), stderr="", exit_code=0,
                                timed_out=False, duration=0, plots=plots,
                                chart_data=extract_plot_output(result.stdout)[3])
    assert execution.success
    assert grade_chart(execution, exercise_id) == (True, None)
    assert base64.b64decode(execution.plots[0]).startswith(b"\x89PNG\r\n\x1a\n")


def test_plot_count_limit_and_invalid_frames():
    result, (_, plots, _) = run_capture(
        "import matplotlib.pyplot as plt\nfor i in range(4):\n plt.figure()\n plt.plot([1,2])\n plt.show()"
    )
    assert result.returncode != 0
    assert len(plots) == MAX_PLOTS
    text, plots, limited = extract_plots(b"hello" + PREFIX + b"aHRtbA==\n")
    assert text == b"hello" and plots == [] and limited


def test_plot_field_rejects_non_png_payload():
    with pytest.raises(ValueError):
        ExecutionResult(stdout="", stderr="", exit_code=0, timed_out=False,
                        duration=0, plots=[base64.b64encode(b"<svg/>").decode()])


@pytest.mark.parametrize("code", [
    'print("")',
    'print("302780 129950 55310 117520")',
    'import matplotlib.pyplot as plt\nplt.plot([1,2,3],[4,5,6])\nplt.show()',
])
def test_empty_output_or_unrelated_plot_does_not_pass(code):
    result, _ = run_capture(code)
    text, plots, limited, chart_data = extract_plot_output(result.stdout)
    execution = ExecutionResult(stdout=text.decode(), stderr=result.stderr.decode(),
        exit_code=result.returncode, timed_out=False, duration=0,
        plots=plots, chart_data=chart_data, output_limited=limited)
    passed, feedback = grade_chart(execution, "lesson_13_python_02")
    assert passed is False and feedback


def test_old_self_review_record_cannot_unlock_expert_for_empty_print(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from app.api.v1.schemas.sandbox import SandboxExecuteRequest
    from app.api.v1.services.sandbox import SandboxService

    old_answer = json.dumps({"type": "code", "language": "python", "check_mode": "self_review", "value": "SECRET"})
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: old_answer)),
                         commit=AsyncMock())
    db.add = Mock(side_effect=lambda row: setattr(row, "attempt_id", 1))
    service = SandboxService(db)
    service.execute = AsyncMock(return_value=ExecutionResult(stdout="\n", stderr="",
        exit_code=0, timed_out=False, duration=0))
    request = SandboxExecuteRequest(code='print("")', course_slug="ai-development-beginner",
        module_id=5, lesson_id=13, exercise_id="lesson_13_python_02", language="python")
    response = asyncio.run(service.submit(request=Mock(), data=request,
        current=SimpleNamespace(user=SimpleNamespace(user_id=1))))
    assert response.is_correct is False
    assert response.expert_solution_available is False
    assert response.check_mode == "graded"
    assert response.feedback
    assert "__expert_review_exercises__" not in db.add.call_args.args[0].answers


def test_old_expert_review_permission_is_not_enough_to_download_expert():
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.api.v1.services.student_exercises import StudentExerciseService

    service = StudentExerciseService(None)
    service.get_exercise = AsyncMock(return_value=SimpleNamespace(
        execution_enabled=True, is_completed=False, expert_solution_available=True,
    ))
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.get_expert_solution(object(), "ai-development-beginner", 5, 13,
            "lesson_13_python_02", object()))
    assert error.value.status_code == 403


def test_correct_chart_passes_even_with_old_self_review_record():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from app.api.v1.schemas.sandbox import SandboxExecuteRequest
    from app.api.v1.services.sandbox import SandboxService

    result, _ = run_capture(references()["lesson_13_python_02"])
    text, plots, limited, chart_data = extract_plot_output(result.stdout)
    execution = ExecutionResult(stdout=text.decode(), stderr=result.stderr.decode(),
        exit_code=result.returncode, timed_out=False, duration=0,
        plots=plots, chart_data=chart_data, output_limited=limited)
    answer = json.dumps({"type": "code", "language": "python", "check_mode": "self_review", "value": "SECRET"})
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: answer)),
                         commit=AsyncMock())
    db.add = Mock(side_effect=lambda row: setattr(row, "attempt_id", 1))
    service = SandboxService(db)
    service.execute = AsyncMock(return_value=execution)
    response = asyncio.run(service.submit(request=Mock(), data=SandboxExecuteRequest(
        code="student code", language="python", lesson_id=13, module_id=5,
        course_slug="ai-development-beginner", exercise_id="lesson_13_python_02",
    ), current=SimpleNamespace(user=SimpleNamespace(user_id=1))))
    assert response.is_correct is True
    assert response.expert_solution_available is True
    assert response.check_mode == "graded"
    assert "lesson_13_python_02" in db.add.call_args.args[0].answers["__passed_exercises__"]


def test_vertical_bar_chart_is_also_accepted():
    code = '''import matplotlib.pyplot as plt
plt.bar(["Электроника", "Аксессуары", "Бытовая техника", "Канцелярия", "Товары для дома"],
        [220000, 37500, 34700, 5540, 5040])
plt.title("RETAIL SALES")
plt.xlabel("Категория")
plt.ylabel("Выручка, руб.")
plt.show()
'''
    result, _ = run_capture(code)
    text, plots, limited, chart_data = extract_plot_output(result.stdout)
    execution = ExecutionResult(stdout=text.decode(), stderr=result.stderr.decode(), exit_code=result.returncode,
        timed_out=False, duration=0, plots=plots, chart_data=chart_data, output_limited=limited)
    assert grade_chart(execution, "lesson_13_python_01")[0] is True


def test_png_survives_student_api_response(monkeypatch):
    import httpx
    from fastapi import FastAPI
    from app.api.v1.routes.sandbox import router
    from app.api.v1.schemas.sandbox import ExerciseSubmissionResponse
    from app.api.v1.services.sandbox import SandboxService
    from app.core.database import get_db
    from app.core.session import get_current_user

    result, (text, plots, _) = run_capture(
        "import matplotlib.pyplot as plt\nplt.plot([1,2],[3,4])\nplt.show()"
    )
    assert result.returncode == 0
    execution = ExecutionResult(stdout=text.decode(), stderr="", plots=plots,
                                exit_code=0, timed_out=False, duration=0)
    monkeypatch.setattr(SandboxService, "submit", AsyncMock(return_value=ExerciseSubmissionResponse(
        execution=execution, execution_succeeded=True, is_correct=None, attempt_id=1,
        expert_solution_available=True, check_mode="self_review",
    )))
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: object()

    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/sandbox/execute", json={
                "code": "pass", "language": "python", "course_slug": "ai-development-beginner",
                "module_id": 5, "lesson_id": 13, "exercise_id": "lesson_13_python_01",
            })

    response = asyncio.run(request())
    assert response.status_code == 200, response.text
    assert response.json()["plots"] == plots
    assert response.json()["check_mode"] == "self_review"
    assert response.json()["expert_solution_available"] is True
