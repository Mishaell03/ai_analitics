"""Интеграционные тесты медиафайлов: загрузка, доступ, удаление.

Тестам нужны поднятые PostgreSQL и MinIO. Если их нет — тесты
пропускаются, чтобы обычный запуск юнит-тестов не падал.
"""

import io

import pytest
from sqlalchemy import select
from starlette.requests import Request

import app.main  # noqa: F401  (регистрация всех моделей)

from app.api.v1.services.lesson_media import LessonMediaService
from app.core.database import AsyncSessionLocal
from app.core.minio_url import minio_storage
from app.core.storage_paths import COURSE_CONTENT_BUCKET
from app.models.enrollments_progress import CourseEnrollment
from app.models.media import LessonMedia, MediaFile

from conftest import LOOP, infrastructure_available
from test_video_inspector import make_mp4

# модуль и уроки из сидов
MODULE_ID = 1
LESSON_ID = 1
OTHER_LESSON_ID = 2

# пользователь, который не записан на курс
NOT_ENROLLED_USER_ID = 1000001

# администратор
ADMIN_ID = 1000002

COURSE_SLUG = "ai-development-beginner"

def run(coroutine):
    """ЗАПУСКАЕТ КОРУТИНУ В СИНХРОННОМ ТЕСТЕ

    Все тесты делят один event loop: подключения asyncpg создаются
    при первом использовании и привязаны к своему loop.
    """

    return LOOP.run_until_complete(coroutine)


def make_request() -> Request:
    """ЗАПРОС ДЛЯ СЕРВИСА"""

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": [(b"host", b"test")],
        "client": ("127.0.0.1", 12345),
        "query_string": b"",
    }

    request = Request(scope)
    request.state.raw_body = None

    return request


class FakeUpload:
    """ФАЙЛ, КАК ЕГО ВИДИТ FASTAPI"""

    def __init__(self, data: bytes, filename: str, content_type: str):
        self.file = io.BytesIO(data)
        self.filename = filename
        self.content_type = content_type
        self.size = len(data)

    async def read(self, size: int = -1) -> bytes:
        return self.file.read(size)


def make_png(size=(400, 300)) -> bytes:
    """ГОТОВИТ PNG ДЛЯ ЗАГРУЗКИ"""

    from PIL import Image

    buffer = io.BytesIO()

    Image.new("RGB", size, (10, 120, 200)).save(buffer, format="PNG")

    return buffer.getvalue()


pytestmark = pytest.mark.skipif(
    not infrastructure_available(),
    reason="нужны поднятые PostgreSQL и MinIO",
)


@pytest.fixture
def media_ids():
    """СОБИРАЕТ СОЗДАННЫЕ ФАЙЛЫ, ЧТОБЫ УДАЛИТЬ ИХ ПОСЛЕ ТЕСТА"""

    created: list[int] = []

    yield created

    async def cleanup():
        async with AsyncSessionLocal() as db:
            for media_id in created:
                media = await db.get(MediaFile, media_id)

                if media is None:
                    continue

                await minio_storage.delete_file(
                    file_path=media.object_key,
                    bucket=COURSE_CONTENT_BUCKET,
                )

                await db.delete(media)

            await db.commit()

    run(cleanup())


def upload_media(file: FakeUpload, lesson_id: int = LESSON_ID, user_id: int = ADMIN_ID):
    """ЗАГРУЖАЕТ ФАЙЛ ЧЕРЕЗ СЕРВИС"""

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await LessonMediaService(db).upload_media(
                request=make_request(),
                course_slug=COURSE_SLUG,
                module_id=MODULE_ID,
                lesson_id=lesson_id,
                file=file,
                language="en",
                user_id=user_id,
            )

    return run(scenario())


def get_media_object_key(media_id: int) -> str:
    """КЛЮЧ ОБЪЕКТА ФАЙЛА В MINIO"""

    async def scenario():
        async with AsyncSessionLocal() as db:
            media = await db.get(MediaFile, media_id)

            return media.object_key

    return run(scenario())


def test_upload_image_creates_media_and_object(media_ids):
    """ЗАГРУЗКА ИЗОБРАЖЕНИЯ СОЗДАЁТ ЗАПИСЬ И ФАЙЛ В MINIO"""

    media = upload_media(FakeUpload(make_png(), "scheme.png", "image/png"))

    media_ids.append(media.media_id)

    assert media.kind == "image"
    assert media.content_type == "image/webp"
    assert media.width == 400
    assert media.height == 300
    assert media.size_bytes > 0
    assert media.url is not None
    assert media.media_key.startswith("m_")

    # файл действительно лежит в хранилище
    object_key = get_media_object_key(media.media_id)

    assert run(
        minio_storage.exists(file_path=object_key, bucket=COURSE_CONTENT_BUCKET)
    ) is True


def test_upload_video_keeps_codecs(media_ids):
    """ЗАГРУЗКА ВИДЕО СОХРАНЯЕТ МЕТАДАННЫЕ КОДЕКОВ"""

    media = upload_media(FakeUpload(make_mp4(), "lesson.mp4", "video/mp4"))

    media_ids.append(media.media_id)

    assert media.kind == "video"
    assert media.content_type == "video/mp4"
    assert media.video_codec == "h264"
    assert media.audio_codec == "aac"
    assert media.width == 1280
    assert media.height == 720
    assert media.duration_seconds == 12.0


def test_upload_rejects_broken_video():
    """ПОДДЕЛАННЫЙ MP4 ОТКЛОНЯЕТСЯ"""

    with pytest.raises(Exception) as error:
        upload_media(FakeUpload(b"not a real mp4", "fake.mp4", "video/mp4"))

    assert error.value.detail["code"] == "MEDIA_FILE_TYPE_NOT_ALLOWED"


def test_upload_rejects_unknown_type():
    """НЕИЗВЕСТНЫЙ ТИП ФАЙЛА ОТКЛОНЯЕТСЯ"""

    with pytest.raises(Exception) as error:
        upload_media(FakeUpload(b"just a text", "doc.txt", "text/plain"))

    assert error.value.detail["code"] == "MEDIA_FILE_TYPE_NOT_ALLOWED"


def test_user_without_enrollment_gets_no_url(media_ids):
    """ПОЛЬЗОВАТЕЛЬ БЕЗ ЗАПИСИ НА КУРС НЕ ПОЛУЧАЕТ ССЫЛКУ"""

    media = upload_media(FakeUpload(make_png(), "private.png", "image/png"))

    media_ids.append(media.media_id)

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await LessonMediaService(db).get_media_url(
                request=make_request(),
                media_key=media.media_key,
                language="en",
                user_id=NOT_ENROLLED_USER_ID,
            )

    with pytest.raises(Exception) as error:
        run(scenario())

    assert error.value.detail["code"] == "COURSE_ACCESS_REQUIRED"


def test_enrolled_user_gets_url(media_ids):
    """ЗАПИСАННЫЙ ПОЛЬЗОВАТЕЛЬ ПОЛУЧАЕТ ССЫЛКУ"""

    media = upload_media(FakeUpload(make_png(), "public.png", "image/png"))

    media_ids.append(media.media_id)

    async def scenario():
        async with AsyncSessionLocal() as db:
            service = LessonMediaService(db)

            enrollment = await db.execute(
                select(CourseEnrollment).where(
                    CourseEnrollment.user_id == 1000000,
                )
            )

            rows = enrollment.scalars().all()

            if not rows:
                pytest.skip("пользователь не записан на курс")

            return await service.get_media_url(
                request=make_request(),
                media_key=media.media_key,
                language="en",
                user_id=1000000,
            )

    url = run(scenario())

    assert url.url.startswith("http")
    assert url.expires_in > 0
    assert url.media_key == media.media_key


def test_delete_media_removes_file_and_links(media_ids):
    """УДАЛЕНИЕ ФАЙЛА УБИРАЕТ ЕГО ИЗ ХРАНИЛИЩА И ИЗ СВЯЗЕЙ"""

    media = upload_media(FakeUpload(make_png(), "to-delete.png", "image/png"))

    media_ids.append(media.media_id)

    object_key = get_media_object_key(media.media_id)

    async def scenario():
        async with AsyncSessionLocal() as db:
            return await LessonMediaService(db).delete_media(
                request=make_request(),
                media_key=media.media_key,
                lesson_id=LESSON_ID,
                language="en",
                user_id=ADMIN_ID,
            )

    run(scenario())

    assert run(
        minio_storage.exists(file_path=object_key, bucket=COURSE_CONTENT_BUCKET)
    ) is False

    async def check_links():
        async with AsyncSessionLocal() as db:
            links = await db.execute(
                select(LessonMedia).where(LessonMedia.media_id == media.media_id)
            )

            return links.scalar_one_or_none()

    assert run(check_links()) is None


def test_media_used_in_two_lessons_is_kept(media_ids):
    """ФАЙЛ, КОТОРЫЙ ИСПОЛЬЗУЕТСЯ В ДВУХ УРОКАХ, НЕ УДАЛЯЕТСЯ СРАЗУ"""

    media = upload_media(FakeUpload(make_png(), "shared.png", "image/png"))

    media_ids.append(media.media_id)

    object_key = get_media_object_key(media.media_id)

    async def scenario():
        async with AsyncSessionLocal() as db:
            service = LessonMediaService(db)

            await service.attach_media(
                request=make_request(),
                lesson_id=OTHER_LESSON_ID,
                media_key=media.media_key,
                language="en",
                user_id=ADMIN_ID,
            )

            # отвязываем от первого урока: файл ещё нужен второму
            await service.delete_media(
                request=make_request(),
                media_key=media.media_key,
                lesson_id=LESSON_ID,
                language="en",
                user_id=ADMIN_ID,
            )

    run(scenario())

    assert run(
        minio_storage.exists(file_path=object_key, bucket=COURSE_CONTENT_BUCKET)
    ) is True

    async def check_links():
        async with AsyncSessionLocal() as db:
            links = await db.execute(
                select(LessonMedia).where(LessonMedia.media_id == media.media_id)
            )

            return links.scalars().all()

    assert len(run(check_links())) == 1
