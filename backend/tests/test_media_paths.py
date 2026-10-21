from app.core.storage_paths import (
    course_cover_object_key,
    generate_file_id,
    generate_media_key,
    is_safe_media_key,
    media_object_key,
)


def test_generated_keys_are_safe():
    media_key = generate_media_key()
    file_id = generate_file_id()

    assert media_key.startswith("m_")
    assert file_id.startswith("c_")
    assert is_safe_media_key(media_key)
    assert is_safe_media_key(file_id)


def test_generated_keys_are_unique():
    assert len({generate_media_key() for _ in range(100)}) == 100


def test_media_object_key():
    assert media_object_key(
        course_id=3,
        media_key="m_0123456789abcdef",
        extension=".webp",
    ) == "3/media/m_0123456789abcdef.webp"


def test_media_object_key_rejects_unsafe_identifier():
    assert media_object_key(
        course_id=3,
        media_key="../../etc/passwd",
        extension=".webp",
    ) is None

    assert media_object_key(
        course_id=3,
        media_key="m_0123456789abcdef",
        extension="../../x",
    ) is None


def test_media_object_key_rejects_unsafe_course_id():
    assert media_object_key(
        course_id=0,
        media_key="m_0123456789abcdef",
        extension=".webp",
    ) is None


def test_course_cover_object_key():
    assert course_cover_object_key(course_id=2) == "2/main.webp"


def test_course_cover_object_key_rejects_unsafe_id():
    assert course_cover_object_key(course_id=0) is None
    assert course_cover_object_key(course_id=-1) is None
