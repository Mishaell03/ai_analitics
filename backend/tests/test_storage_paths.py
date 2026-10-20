from app.core.storage_paths import (
    is_safe_slug,
    lesson_asset_path,
    lesson_assets_prefix,
    lesson_content_path,
)


def test_lesson_content_path():
    assert lesson_content_path(
        course_slug="ai-development-beginner",
        module_id=2,
        lesson_id=7,
    ) == "ai-development-beginner/2/7.md"


def test_lesson_content_path_of_unsafe_slug():
    assert lesson_content_path("../secrets", 1, 1) is None
    assert lesson_content_path("course/../../etc", 1, 1) is None
    assert lesson_content_path("", 1, 1) is None


def test_lesson_assets_prefix():
    assert lesson_assets_prefix("ai-development-beginner", 2) == (
        "ai-development-beginner/2/assets/"
    )


def test_lesson_asset_path():
    assert lesson_asset_path("ai-development-beginner", 2, "schema.png") == (
        "ai-development-beginner/2/assets/schema.png"
    )


def test_lesson_asset_path_rejects_traversal():
    assert lesson_asset_path("ai-development-beginner", 2, "../secret.png") is None
    assert lesson_asset_path("ai-development-beginner", 2, "nested/schema.png") is None
    assert lesson_asset_path("ai-development-beginner", 2, "..") is None


def test_is_safe_slug():
    assert is_safe_slug("ai-development-beginner")
    assert is_safe_slug("course_847b19c3")
    assert not is_safe_slug("course 847b19c3")
    assert not is_safe_slug("../course")
    assert not is_safe_slug("")
