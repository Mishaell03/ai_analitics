"""ПЕРЕНОС СТАРЫХ ФАЙЛОВ В РАСКЛАДКУ COURSE-CONTENT

Раньше файлы курса лежали в нескольких баках:

    course-media/covers/{course_id}/{file_id}.webp
    course-media/media/{course_id}/{media_key}.webp
    lesson-content/{course_slug}/{module_id}/{lesson_id}.md
    module-content/{module_id}/content.md

Теперь всё лежит в одном баке `course-content` внутри каталога курса.
Миграция идемпотентна: её можно запускать при каждом старте приложения.

Порядок безопасный — сначала объект копируется, затем проверяется,
что копия появилась, и только после этого удаляется старый объект.
Для записей БД старый объект удаляется после коммита нового ключа.
"""

import logging
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.minio_url import minio_storage
from app.core.storage_paths import (
    COURSE_CONTENT_BUCKET,
    course_cover_object_key,
    lesson_content_path,
    media_object_key,
    module_content_path,
)
from app.models.courses import CourseModule, Lesson
from app.models.media import CourseImage, MediaFile

# старые баки: имена используются только здесь, в коде миграции
LEGACY_MEDIA_BUCKET = "course-media"
LEGACY_LESSON_BUCKET = "lesson-content"
LEGACY_MODULE_BUCKET = "module-content"

# расширения файлов, которые могли лежать в старом баке медиа
_IMAGE_EXTENSIONS = frozenset({".webp", ".jpg", ".jpeg", ".png", ".gif", ".bmp"})
_VIDEO_EXTENSIONS = frozenset({".mp4"})


async def migrate_legacy_storage() -> dict[str, int]:
    """ПЕРЕНОСИТ СТАРЫЕ ОБЪЕКТЫ В COURSE-CONTENT

    Ошибка в одном разделе не мешает остальным: приложение должно
    запуститься, даже если хранилище временно недоступно.
    """

    stats = {
        "covers": 0,
        "orphan_covers": 0,
        "media": 0,
        "module_content": 0,
        "lessons": 0,
    }

    if not await minio_storage.ensure_bucket(COURSE_CONTENT_BUCKET):
        logging.warning("minio migration skipped: course-content is unavailable")

        return stats

    steps = (
        ("covers", _migrate_covers, stats),
        ("media", _migrate_media, stats),
        ("module content", _migrate_module_content, stats),
        ("lesson content", _migrate_lesson_content, stats),
    )

    for title, step, step_stats in steps:
        try:
            result = await step()

        except Exception:
            logging.exception(f"minio migration failed: {title}")

            continue

        for key, value in result.items():
            step_stats[key] += value

    logging.info(f"minio migration finished: {stats}")

    return stats


async def _migrate_covers() -> dict[str, int]:
    """ОБЛОЖКИ: course-media/covers/... -> course-content/{course_id}/main.webp"""

    stats = {"covers": 0, "orphan_covers": 0}

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CourseImage))
        images = result.scalars().all()

        course_ids_with_cover = {image.course_id for image in images}

        for image in images:
            target_key = course_cover_object_key(course_id=image.course_id)

            if target_key is None or image.object_key == target_key:
                continue

            source_bucket = (
                LEGACY_MEDIA_BUCKET
                if image.object_key.startswith("covers/")
                else COURSE_CONTENT_BUCKET
            )

            if not await _copy_verified(
                source_bucket=source_bucket,
                source_key=image.object_key,
                target_key=target_key,
                overwrite=True,
            ):
                continue

            old_key = image.object_key

            image.object_key = target_key

            await db.commit()

            await minio_storage.delete_file(
                file_path=old_key,
                bucket=source_bucket,
            )

            stats["covers"] += 1

    # обложки без записи в БД: переносим только однозначные случаи
    legacy_keys = await minio_storage.list_keys(
        bucket=LEGACY_MEDIA_BUCKET,
        prefix="covers/",
    )

    groups: dict[int, list[str]] = {}

    for key in legacy_keys:
        parts = key.split("/")

        if len(parts) != 3 or not parts[1].isdigit():
            continue

        groups.setdefault(int(parts[1]), []).append(key)

    for course_id, keys in groups.items():
        if course_id in course_ids_with_cover:
            continue

        target_key = course_cover_object_key(course_id=course_id)

        if target_key is None or await minio_storage.exists(
            file_path=target_key,
            bucket=COURSE_CONTENT_BUCKET,
        ):
            continue

        if len(keys) != 1:
            logging.warning(
                f"minio migration skipped ambiguous covers: course={course_id}"
            )

            continue

        if await _copy_verified(
            source_bucket=LEGACY_MEDIA_BUCKET,
            source_key=keys[0],
            target_key=target_key,
            overwrite=False,
        ):
            await minio_storage.delete_file(
                file_path=keys[0],
                bucket=LEGACY_MEDIA_BUCKET,
            )

            stats["orphan_covers"] += 1

    return stats


async def _migrate_media() -> dict[str, int]:
    """МЕДИА: course-media/media/... -> course-content/{course_id}/media/..."""

    stats = {"media": 0}

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MediaFile))
        media_files = result.scalars().all()

        for media in media_files:
            extension = _media_extension(media)

            target_key = media_object_key(
                course_id=media.course_id,
                media_key=media.media_key,
                extension=extension,
            )

            if target_key is None or media.object_key == target_key:
                continue

            source_bucket = (
                LEGACY_MEDIA_BUCKET
                if media.object_key.startswith("media/")
                else COURSE_CONTENT_BUCKET
            )

            if not await _copy_verified(
                source_bucket=source_bucket,
                source_key=media.object_key,
                target_key=target_key,
                overwrite=True,
            ):
                continue

            old_key = media.object_key

            media.object_key = target_key

            await db.commit()

            await minio_storage.delete_file(
                file_path=old_key,
                bucket=source_bucket,
            )

            stats["media"] += 1

    return stats


async def _migrate_module_content() -> dict[str, int]:
    """ВВОДНЫЙ ТЕКСТ МОДУЛЯ: module-content -> course-content/{course_id}/{module_id}"""

    stats = {"module_content": 0}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CourseModule.module_id, CourseModule.course_id)
        )

        for module_id, course_id in result.all():
            source_key = f"{module_id}/content.md"

            target_key = module_content_path(
                course_id=course_id,
                module_id=module_id,
            )

            if target_key is None:
                continue

            if not await minio_storage.exists(
                file_path=source_key,
                bucket=LEGACY_MODULE_BUCKET,
            ):
                continue

            if not await _copy_verified(
                source_bucket=LEGACY_MODULE_BUCKET,
                source_key=source_key,
                target_key=target_key,
                overwrite=False,
            ):
                continue

            await minio_storage.delete_file(
                file_path=source_key,
                bucket=LEGACY_MODULE_BUCKET,
            )

            stats["module_content"] += 1

    return stats


async def _migrate_lesson_content() -> dict[str, int]:
    """MARKDOWN УРОКОВ: lesson-content/{slug}/{module_id}/{lesson_id}.md

    Старый путь начинался со slug курса, который могли переименовать.
    Поэтому уроки ищем по числовым id в БД, а не по slug в ключе.
    """

    stats = {"lessons": 0}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Lesson.lesson_id,
                Lesson.module_id,
                CourseModule.course_id,
            )
            .join(CourseModule, CourseModule.module_id == Lesson.module_id)
        )

        lesson_courses = {
            (module_id, lesson_id): course_id
            for lesson_id, module_id, course_id in result.all()
        }

    legacy_keys = await minio_storage.list_keys(
        bucket=LEGACY_LESSON_BUCKET,
    )

    for key in legacy_keys:
        parts = key.split("/")

        if len(parts) != 3 or not parts[2].endswith(".md"):
            continue

        module_part, lesson_part = parts[1], parts[2][:-3]

        if not module_part.isdigit() or not lesson_part.isdigit():
            continue

        module_id = int(module_part)
        lesson_id = int(lesson_part)

        course_id = lesson_courses.get((module_id, lesson_id))

        if course_id is None:
            continue

        target_key = lesson_content_path(
            course_id=course_id,
            module_id=module_id,
            lesson_id=lesson_id,
        )

        if target_key is None:
            continue

        if not await _copy_verified(
            source_bucket=LEGACY_LESSON_BUCKET,
            source_key=key,
            target_key=target_key,
            overwrite=False,
        ):
            continue

        await minio_storage.delete_file(
            file_path=key,
            bucket=LEGACY_LESSON_BUCKET,
        )

        stats["lessons"] += 1

    return stats


async def _copy_verified(
    source_bucket: str,
    source_key: str,
    target_key: str,
    overwrite: bool,
) -> bool:
    """КОПИРУЕТ ОБЪЕКТ И ПРОВЕРЯЕТ, ЧТО КОПИЯ ПОЯВИЛАСЬ"""

    if source_bucket == COURSE_CONTENT_BUCKET and source_key == target_key:
        return True

    # при переносе урока новый файл, сохранённый уже в новой раскладке,
    # не перезаписываем старой копией
    if not overwrite and await minio_storage.exists(
        file_path=target_key,
        bucket=COURSE_CONTENT_BUCKET,
    ):
        return True

    if not await minio_storage.exists(
        file_path=source_key,
        bucket=source_bucket,
    ):
        return False

    if not await minio_storage.copy_object(
        source_bucket=source_bucket,
        source_path=source_key,
        target_bucket=COURSE_CONTENT_BUCKET,
        target_path=target_key,
    ):
        return False

    return await minio_storage.exists(
        file_path=target_key,
        bucket=COURSE_CONTENT_BUCKET,
    )


def _media_extension(media: MediaFile) -> str:
    """РАСШИРЕНИЕ ФАЙЛА МЕДИА ДЛЯ НОВОГО КЛЮЧА"""

    suffix = Path(media.object_key).suffix.lower()

    if suffix in _IMAGE_EXTENSIONS or suffix in _VIDEO_EXTENSIONS:
        return suffix

    if media.kind == "video":
        return ".mp4"

    return ".webp"


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    asyncio.run(migrate_legacy_storage())
