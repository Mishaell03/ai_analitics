from app.core.storage_paths import (
    course_content_path,
    course_prefix,
    lesson_content_path,
    media_prefix,
    module_content_path,
    module_prefix,
)


def test_course_prefix():
    assert course_prefix(3) == "3/"
    assert course_prefix(0) is None
    assert course_prefix(-1) is None


def test_module_prefix():
    assert module_prefix(3, 7) == "3/7/"
    assert module_prefix(3, 0) is None


def test_media_prefix():
    assert media_prefix(3) == "3/media/"
    assert media_prefix(0) is None


def test_lesson_content_path():
    assert lesson_content_path(
        course_id=3,
        module_id=2,
        lesson_id=7,
    ) == "3/2/7.md"


def test_lesson_content_path_rejects_unsafe_ids():
    assert lesson_content_path(0, 1, 1) is None
    assert lesson_content_path(1, 0, 1) is None
    assert lesson_content_path(1, 1, 0) is None
    assert lesson_content_path(True, 1, 1) is None


def test_module_content_path():
    assert module_content_path(course_id=3, module_id=2) == "3/2/content.md"
    assert module_content_path(course_id=0, module_id=2) is None


def test_course_content_path():
    assert course_content_path(course_id=3) == "3/content.md"
    assert course_content_path(course_id=0) is None
