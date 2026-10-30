"""Checks course Python exercises and answers without DB, MinIO or Docker."""

import ast
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.markdown import MarkdownParser


ROOT = Path(__file__).resolve().parents[1]
SEED_ROOT = ROOT / "infra/postgres/core_db/seeds"
LESSONS = (
    (4, 4, "1/2/4.md"),
    (5, 5, "1/2/5.md"),
    (6, 6, "1/2/6.md"),
    (7, 7, "1/3/7.md"),
    (8, 8, "1/3/8.md"),
    (10, 10, "1/3/10.md"),
)


def _seed_code_answers(sequence: int) -> dict[str, tuple[str, str]]:
    """Returns exercise_id -> (reference code, expected stdout) from SQL seed."""
    source = (SEED_ROOT / f"R__lesson_{sequence:02d}_answers.sql").read_text(encoding="utf-8")
    rows = re.findall(
        rf"\('(lesson_{sequence:02d}_python_\w+)', \$python\$(.*?)\$python\$, E'((?:\\.|[^'])*)'\)",
        source,
        re.S,
    )
    return {
        exercise_id: (code, ast.literal_eval('"' + stdout + '"'))
        for exercise_id, code, stdout in rows
    }


def test_python_exercise_ids_match_markdown_and_reference_seeds():
    parser = MarkdownParser()
    for sequence, _database_id, relative_path in LESSONS:
        content_path = ROOT / "infra/minio/seeds/course-content" / relative_path
        content = content_path.read_text(encoding="utf-8")
        parsed = parser.parse(content)
        code_blocks = {
            block.data["exercise_id"]: block.data["language"]
            for block in parsed.custom_blocks
            if block.type == "code" and block.data and not block.data.get("practice")
        }
        references = _seed_code_answers(sequence)

        assert code_blocks == {exercise_id: "python" for exercise_id in references}, (
            f"{content_path}: Markdown code IDs and SQL reference IDs differ; "
            f"blocks={sorted(code_blocks)}, references={sorted(references)}"
        )
        for exercise_id, (code, _) in references.items():
            compile(code, exercise_id, "exec")
            if exercise_id != "lesson_04_python_intro":
                assert code.strip() not in content, f"{exercise_id}: reference code leaked into Markdown"


@pytest.mark.parametrize("sequence,_database_id,_relative_path", LESSONS)
def test_python_reference_code_runs(sequence, _database_id, _relative_path):
    references = _seed_code_answers(sequence)
    assert references, f"Lesson {sequence}: no Python references found in SQL seed"
    if sequence in (7, 8, 10) and importlib.util.find_spec("pandas") is None:
        pytest.skip("pandas is absent from the local venv; it is installed in the sandbox image")

    for exercise_id, (code, expected_stdout) in references.items():
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-c", code],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise AssertionError(f"{exercise_id}: reference code exceeded 5 seconds") from error

        assert result.returncode == 0, f"{exercise_id}: {result.stderr}"
        assert result.stderr == "", f"{exercise_id}: unexpected stderr: {result.stderr}"
        assert result.stdout == expected_stdout, (
            f"{exercise_id}: stdout mismatch\n"
            f"expected: {expected_stdout!r}\nactual:   {result.stdout!r}"
        )


def test_lesson_10_reference_business_rules():
    """Check actual data selections as well as captured output of the references."""
    pytest.importorskip("pandas")
    checks = {
        "lesson_10_python_01": """
assert df.shape == (6, 5)
assert df.loc[df['quantity'].isna(), 'line_item_id'].tolist() == [6103]
assert df.loc[duplicate_mask, 'line_item_id'].tolist() == [6104, 6104]
assert df.loc[duplicate_mask, 'order_id'].tolist() == [8103, 8104]
assert df['order_id'].value_counts().loc[8101] == 2
""",
        "lesson_10_python_02": """
assert df['quantity'].tolist() == [1, 2, 3, 4, 15]
assert df['quantity'].mean() == 5
assert df['quantity'].median() == 3
assert df['quantity'].min() == 1
assert df['quantity'].max() == 15
""",
        "lesson_10_python_03": """
assert df.shape == (9, 9)
assert df.loc[df['quantity'].isna(), 'line_item_id'].tolist() == [7305]
assert df.loc[df['quantity'] <= 0, 'line_item_id'].tolist() == [7304]
assert df.loc[df['unit_price'] < 0, 'line_item_id'].tolist() == [7306]
assert df.loc[unknown_status_mask, 'line_item_id'].tolist() == [7307]
assert df.loc[duplicate_mask, 'line_item_id'].tolist() == [7308, 7308]
assert valid_df['line_item_id'].tolist() == [7301, 7302, 7303]
assert valid_df['quantity'].tolist() == [2, 3, 1]
assert valid_df['quantity'].mean() == valid_df['quantity'].median() == 2
assert valid_df['quantity'].min() == 1
assert valid_df['quantity'].max() == 3
""",
    }
    for exercise_id, (code, _) in _seed_code_answers(10).items():
        result = subprocess.run(
            [sys.executable, "-I", "-c", code + "\n" + checks[exercise_id]],
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        assert result.returncode == 0, f"{exercise_id}: {result.stderr}"


@pytest.mark.parametrize(
    "sequence,database_id,relative_path,option_numbers",
    [
        (7, 7, "1/3/7.md", [3, 1, 4, 2, 3, 2]),
        (8, 8, "1/3/8.md", [3, 2, 4, 1, 3, 2]),
        (9, 9, "1/3/9.md", [2, 4, 1, 3, 2, 2]),
        (10, 10, "1/3/10.md", [2, 3, 2, 4, 1, 3]),
    ],
)
def test_course_test_answers_match_markdown_options(sequence, database_id, relative_path, option_numbers):
    content = (ROOT / "infra/minio/seeds/course-content" / relative_path).read_text(encoding="utf-8")
    seed = (SEED_ROOT / f"R__lesson_{sequence:02d}_answers.sql").read_text(encoding="utf-8")
    blocks = re.findall(r":::test\s*\nid: ([\w-]+)\n(.*?)\n:::", content, re.S)
    assert len(blocks) == 6
    for (exercise_id, body), option_number in zip(blocks, option_numbers):
        options = re.findall(r"^- \( \) (.*)$", body, re.M)
        answer = re.search(rf"\({database_id}, '{exercise_id}', '(.*?)'\)", seed)
        assert answer is not None, f"Missing answer for {exercise_id}"
        assert json.loads(answer[1])["correct"] == [options[option_number - 1]], exercise_id


def test_pandas_module_and_lessons_keep_requested_ids():
    source = (SEED_ROOT / "R__courses.sql").read_text(encoding="utf-8")
    assert "'Модуль 3. Обработка и анализ данных с помощью pandas'" in source
    assert re.search(r"\(\s*3,\s*\(SELECT course_id FROM courses WHERE slug = 'ai-development-beginner'\)", source)
    assert re.search(r"VALUES \(\s*7,\s*3,", source)
    assert re.search(r"VALUES \(\s*8,\s*3,", source)
    assert re.search(r"VALUES \(\s*9,\s*3,", source)


def test_course_1_seed_matches_all_markdown_paths():
    """Every lesson directory under course-content/1 has a matching DB course/module/lesson mapping."""
    source = (SEED_ROOT / "R__courses.sql").read_text(encoding="utf-8")
    guard = re.search(
        r"JOIN \(VALUES(.*?)\) AS seed\(lesson_id, module_id, position\)", source, re.S
    )
    assert guard is not None
    mapped_rows = {
        tuple(map(int, values))
        for values in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", guard[1])
    }

    content_root = ROOT / "infra/minio/seeds/course-content/1"
    expected_modules = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9, 10], 4: [11, 12], 5: [13, 14]}
    actual_modules = {}
    for module_dir in (content_root / str(module_id) for module_id in expected_modules):
        actual_modules[int(module_dir.name)] = sorted(int(path.stem) for path in module_dir.glob("*.md"))
    assert actual_modules == expected_modules

    expected_mapping = {
        (lesson_id, module_id, position)
        for module_id, lesson_ids in expected_modules.items()
        for position, lesson_id in enumerate(lesson_ids, start=1)
    }
    assert expected_mapping <= mapped_rows

    # Course 1 must publish every lesson found in its MinIO content tree.
    for lesson_id, module_id, _position in expected_mapping:
        if module_id in expected_modules:
            assert re.search(
                rf"\b{lesson_id},\s*{module_id},", source
            ) or re.search(rf"VALUES \(\s*{lesson_id},\s*{module_id},", source), (
                f"No active lesson seed row for course 1 lesson {lesson_id} in module {module_id}"
            )
