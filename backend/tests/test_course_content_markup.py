"""Course Markdown practice fields and media links work without external services."""

import re
import struct
from pathlib import Path

import pytest

from app.core.markdown import MarkdownParser


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "infra/minio/seeds/course-content/1"
SEEDS = ROOT / "infra/postgres/core_db/seeds"


def test_empty_python_fields_have_unique_generated_ids():
    source = "::: code python\n:::\n\n::: code python\n:::"
    parsed = MarkdownParser().parse(source)
    assert parsed.content == source
    assert [block.data["exercise_id"] for block in parsed.custom_blocks] == [
        "practice_python_1", "practice_python_4",
    ]
    assert all(block.data["practice"] for block in parsed.custom_blocks)
    assert all(block.data["language"] == "python" for block in parsed.custom_blocks)


def test_course_has_no_editor_placeholders_and_media_files_exist():
    parser = MarkdownParser()
    seeds = "\n".join(path.read_text(encoding="utf-8") for path in SEEDS.glob("*.sql"))
    for path in CONTENT.glob("[0-9]*/*.md"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"МЕСТО ДЛЯ|Редакторская метка", text), path
        parsed = parser.parse(text)
        for asset in parsed.assets:
            files = list((CONTENT / "media").glob(f"{asset.asset_id}.*"))
            assert len(files) == 1, (path, asset.asset_id)
            assert f"1/media/{files[0].name}" in seeds
            assert asset.asset_id in seeds
        ids = [b.data["exercise_id"] for b in parsed.custom_blocks if b.data and b.data.get("exercise_id")]
        assert len(ids) == len(set(ids)), path


def test_empty_directive_inside_fenced_example_is_not_a_practice_field():
    parsed = MarkdownParser().parse("````markdown\n::: code python\n:::\n````")
    assert not parsed.custom_blocks


@pytest.mark.parametrize("language", ["python", "sql"])
def test_none_directives_have_distinct_practice_ids_and_need_no_references(language):
    from app.api.v1.services.lesson_code_content import validate_blocks

    source = f":::code {language}\nid: none\n:::\n\n::: code {language}\nid: none\n:::"
    parsed = validate_blocks(source, [])
    ids = [block.data["exercise_id"] for block in parsed.custom_blocks]
    assert len(set(ids)) == 2
    assert all(block.data["practice"] for block in parsed.custom_blocks)
    assert all(block.data["language"] == language for block in parsed.custom_blocks)
    assert all(exercise_id.startswith(f"practice_{language}_") for exercise_id in ids)
    assert parsed.content == source


def test_all_course_code_fields_have_explicit_ids():
    for path in CONTENT.glob("[0-9]*/*.md"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^:::\s*code (?:python|sql)\s*\n:::", text, re.M), path


def test_lesson_10_reuses_existing_media():
    source = (SEEDS / "R__lesson_10_answers.sql").read_text(encoding="utf-8")
    assert "SELECT 10, media_id FROM media_files" in source
    assert "media_key = 'm_72e62512f7eb46e3'" in source
    assert "(asset:m_72e62512f7eb46e3)" in (CONTENT / "3/10.md").read_text(encoding="utf-8")


def test_course_lesson_titles_match_markdown_and_use_numbered_format():
    seed = (SEEDS / "R__courses.sql").read_text(encoding="utf-8")
    paths = list(CONTENT.glob("[0-9]*/*.md"))
    assert len(paths) == 14
    for path in paths:
        heading = path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
        assert re.match(r"Урок \d+\. \S", heading), path
        assert f"'{heading}'" in seed, path


@pytest.mark.parametrize("lesson,key", [
    (11, "m_72e62512f7eb67e3"),
    (12, "m_45e57512f7eb46e0"),
])
def test_sql_lesson_media_metadata_matches_real_files(lesson, key):
    seed = (SEEDS / "R__lesson_sql_media.sql").read_text(encoding="utf-8")
    path = CONTENT / "media" / f"{key}.png"
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert f"'image', 'image/png', {len(data)}, {width}, {height}" in seed
    assert f"'1/media/{key}.png'" in seed
    assert f"({lesson}, '{key}')" in seed
    assert f"(asset:{key})" in (CONTENT / "4" / f"{lesson}.md").read_text(encoding="utf-8")
