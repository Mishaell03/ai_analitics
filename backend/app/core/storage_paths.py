"""ПРАВИЛА РАСКЛАДКИ ФАЙЛОВ В MINIO

Единое место, где описано, как лежат файлы курса в баках:

    lesson-content/
        {course_slug}/{module_id}/{lesson_id}.md   — Markdown урока
        {course_slug}/{module_id}/assets/...        — медиафайлы модуля

    course-media/                                 — приватный бак с медиа
        media/{course_id}/{media_key}.webp         — изображения уроков
        media/{course_id}/{media_key}.mp4          — видео уроков
        covers/{course_id}/{file_id}.webp          — обложки курсов

Пути строятся только по проверенным данным (slug из БД, числовые id,
сгенерированные идентификаторы), поэтому в них не может оказаться
выход за пределы бака.
"""

import re
import uuid

# бак с контентом уроков
LESSON_CONTENT_BUCKET = "lesson-content"

# бак с медиафайлами (приватный)
MEDIA_BUCKET = "course-media"

# каталог медиафайлов внутри бака
MEDIA_DIR_NAME = "media"

# каталог обложек курсов внутри бака
COVERS_DIR_NAME = "covers"

# каталог медиафайлов внутри модуля
ASSETS_DIR_NAME = "assets"

# ссылка на медиафайл в Markdown: ![описание](asset:media_key)
ASSET_REFERENCE_PREFIX = "asset:"

# расширение файла с Markdown урока
MARKDOWN_EXTENSION = ".md"

# slug курса используется как часть пути, поэтому в нём допустимы
# только буквы, цифры, дефис и подчёркивание
_SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")

# логические идентификаторы файлов генерируются сервером,
# поэтому в ключе объекта допустимы только буквы, цифры и дефис
_SAFE_FILE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")


def is_safe_slug(course_slug: str) -> bool:
    """БЕЗОПАСЕН ЛИ SLUG ДЛЯ ИСПОЛЬЗОВАНИЯ В ПУТИ"""

    return bool(_SAFE_SLUG_RE.fullmatch(course_slug or ""))


def is_safe_media_key(media_key: str) -> bool:
    """БЕЗОПАСЕН ЛИ ИДЕНТИФИКАТОР МЕДИАФАЙЛА

    Идентификатор попадает в ключ объекта и в ссылки Markdown,
    поэтому проверяется по тому же правилу, что и остальные идентификаторы.
    """

    return bool(_SAFE_FILE_ID_RE.fullmatch(media_key or ""))


def generate_media_key() -> str:
    """ЛОГИЧЕСКИЙ ИДЕНТИФИКАТОР МЕДИАФАЙЛА

    Идентификатор не зависит от пути в MinIO: файл можно перенести
    в другое место, а ссылка в Markdown останется рабочей.
    """

    return f"m_{uuid.uuid4().hex[:16]}"


def generate_file_id() -> str:
    """ЛОГИЧЕСКИЙ ИДЕНТИФИКАТОР ФАЙЛА ОБЛОЖКИ"""

    return f"c_{uuid.uuid4().hex[:16]}"


def lesson_content_path(
        course_slug: str,
        module_id: int,
        lesson_id: int,
) -> str | None:
    """ПУТЬ К MARKDOWN УРОКА В БАКЕ

    None, если slug курса нельзя использовать как часть пути:
    такой урок нельзя прочитать и нельзя выдать ссылкой.
    """

    if not is_safe_slug(course_slug):
        return None

    return f"{course_slug}/{module_id}/{lesson_id}{MARKDOWN_EXTENSION}"


def lesson_assets_prefix(
        course_slug: str,
        module_id: int,
) -> str | None:
    """ПРЕФИКС КАТАЛОГА МЕДИАФАЙЛОВ МОДУЛЯ"""

    if not is_safe_slug(course_slug):
        return None

    return f"{course_slug}/{module_id}/{ASSETS_DIR_NAME}/"


def lesson_asset_path(
        course_slug: str,
        module_id: int,
        file_name: str,
) -> str | None:
    """ПУТЬ К МЕДИАФАЙЛУ МОДУЛЯ В БАКЕ"""

    prefix = lesson_assets_prefix(
        course_slug=course_slug,
        module_id=module_id,
    )

    if prefix is None:
        return None

    if not file_name or "/" in file_name or file_name in {".", ".."}:
        return None

    return f"{prefix}{file_name}"


def media_object_key(
        course_id: int,
        media_key: str,
        extension: str,
) -> str | None:
    """КЛЮЧ ОБЪЕКТА МЕДИАФАЙЛА В БАКЕ

    Идентификатор приходит с сервера, но проверяется на всякий случай:
    в ключ объекта не должно попасть ничего, кроме безопасных символов.
    """

    if not _SAFE_FILE_ID_RE.fullmatch(media_key or ""):
        return None

    if not extension.startswith(".") or not extension[1:].isalnum():
        return None

    return f"{MEDIA_DIR_NAME}/{course_id}/{media_key}{extension}"


def course_cover_object_key(
        course_id: int,
        file_id: str,
        extension: str = ".webp",
) -> str | None:
    """КЛЮЧ ОБЪЕКТА ОБЛОЖКИ КУРСА В БАКЕ"""

    if not _SAFE_FILE_ID_RE.fullmatch(file_id or ""):
        return None

    if not extension.startswith(".") or not extension[1:].isalnum():
        return None

    return f"{COVERS_DIR_NAME}/{course_id}/{file_id}{extension}"
