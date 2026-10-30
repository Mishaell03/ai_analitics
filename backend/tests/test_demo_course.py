"""Demo catalog priority, content paths and media without external services."""

import asyncio
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

from PIL import Image
import pytest
from sqlalchemy import create_engine, select

from app.api.v1.services.courses import BaseCoursesService
from app.core.markdown import MarkdownParser
from app.core.storage_paths import is_safe_media_key, lesson_content_path
from app.models.courses import Course
from app.models.users import User  # noqa: F401 — register relationships before compiling ORM queries
from app.models.auth import UserSession  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "infra/minio/seeds/course-content/4"
SEED = ROOT / "infra/postgres/core_db/seeds/R__demo_course.sql"


def test_demo_course_sort_order_does_not_require_reassigning_ids():
    engine = create_engine("sqlite://")
    Course.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(Course.__table__.insert(), [
            dict(course_id=n, slug=f"course-{n}", title=f"Course {n}",
                 is_published=True, sort_order=0 if n == 4 else 100)
            for n in (1, 2, 3, 4)
        ])
        ids = connection.execute(select(Course.course_id).order_by(Course.sort_order, Course.course_id)).scalars().all()
        assert ids == [4, 1, 2, 3]
    engine.dispose()


@pytest.mark.parametrize("view", ["catalog", "enrolled", "admin"])
def test_course_list_queries_apply_priority_before_pagination(view):
    empty = SimpleNamespace(all=lambda: [], scalars=lambda: SimpleNamespace(all=lambda: []))
    db = SimpleNamespace(execute=AsyncMock(side_effect=[SimpleNamespace(scalar_one=lambda: 0), empty]))
    service = BaseCoursesService(db)
    service._get_cover_urls = AsyncMock(return_value={})
    if view == "admin":
        asyncio.run(service.get_courses_admin())
    else:
        asyncio.run(service.get_courses(user_id=1 if view == "enrolled" else None,
                                       enrolled_only=view == "enrolled"))
    statement = db.execute.call_args_list[1].args[0]
    sql = str(statement)
    assert "ORDER BY courses.sort_order," in sql
    assert sql.index("ORDER BY courses.sort_order,") < sql.index("LIMIT")


def test_demo_slide_references_and_real_image_metadata():
    source = (CONTENT / "11/24.md").read_text(encoding="utf-8")
    seed = SEED.read_text(encoding="utf-8")
    parsed = MarkdownParser().parse(source)
    keys = [asset.asset_id for asset in parsed.assets]
    assert len(keys) == len(set(keys)) == 10
    assert ":::slides" in source
    for key in keys:
        path = CONTENT / "media" / f"{key}.webp"
        with Image.open(path) as image:
            width, height = image.size
        assert f"'image', 'image/webp', {path.stat().st_size}, {width}, {height}" in seed
        assert f"'4/media/{key}.webp'" in seed
    assert "SELECT 24, media_id FROM media_files" in seed
    assert lesson_content_path(4, 11, 24) == "4/11/24.md"
    assert lesson_content_path(4, 11, 25) == "4/11/25.md"


def test_demo_video_registered_without_fake_dimensions_before_upload():
    seed = SEED.read_text(encoding="utf-8")
    key = "m_bb0da2e8512e430r"
    assert is_safe_media_key(key)
    assert f"(asset:{key})" in (CONTENT / "11/25.md").read_text(encoding="utf-8")
    assert f"'4/media/{key}.mp4', 'video', 'video/mp4', 0" in seed
    assert "SELECT 25, media_id FROM media_files" in seed
    assert not (CONTENT / "media" / f"{key}.mp4").exists()


def test_demo_seed_does_not_reuse_ids_from_existing_courses():
    existing = (ROOT / "infra/postgres/core_db/seeds/R__courses.sql").read_text()
    demo = SEED.read_text()
    assert "VALUES (4, 'platform-demo'" in demo
    assert "TRUE, 0)" in demo
    assert "VALUES (11, 4, 'Модуль 1." in demo
    assert "(24, 11, 'Урок 1." in demo
    assert "(25, 11, 'Урок 2." in demo
    assert not re.search(r"VALUES \(11, 4, 'Модуль", existing)
    assert not re.search(r"\(24, \d+, 'Урок|\(25, \d+, 'Урок", existing)
