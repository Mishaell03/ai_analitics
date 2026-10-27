"""ПРАВИЛА РАСКЛАДКИ ФАЙЛОВ КУРСА В MINIO

Все файлы курса лежат в одном баке `course-content`, внутри каталога
курса `{course_id}/`:

    course-content/
        {course_id}/main.webp                       — обложка курса
        {course_id}/content.md                      — вводный текст курса
        {course_id}/{module_id}/content.md          — вводный текст модуля
        {course_id}/{module_id}/{lesson_id}.md      — Markdown урока
        {course_id}/media/{media_key}.webp|.mp4     — медиафайлы урока

Пути строятся только по числовым id из БД и сгенерированным
идентификаторам, поэтому в них не может оказаться выход за пределы бака.
"""

import re
import uuid

# единственный бак с файлами курсов
COURSE_CONTENT_BUCKET = "course-content"

# каталог медиафайлов внутри каталога курса
MEDIA_DIR_NAME = "media"

# каталог медиафайлов внутри модуля (поддерживается Markdown-парсером)
ASSETS_DIR_NAME = "assets"

# ссылка на медиафайл в Markdown: ![описание](asset:media_key)
ASSET_REFERENCE_PREFIX = "asset:"

# расширение файла с Markdown урока
MARKDOWN_EXTENSION = ".md"

# имя файла обложки курса
COVER_FILE_NAME = "main.webp"

# имя файла с вводным текстом курса или модуля
CONTENT_FILE_NAME = "content.md"

# логические идентификаторы файлов генерируются сервером,
# поэтому в ключе объекта допустимы только буквы, цифры и дефис
_SAFE_FILE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")


def _is_safe_id(value: int) -> bool:
    """ПОЛОЖИТЕЛЬНЫЙ ЧИСЛОВОЙ ID ДЛЯ ИСПОЛЬЗОВАНИЯ В ПУТИ"""

    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


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
    """ЛОГИЧЕСКИЙ ИДЕНТИФИКАТОР ФАЙЛА ОБЛОЖКИ

    Используется только как стабильный id записи в БД: путь обложки
    фиксирован и от него не зависит.
    """

    return f"c_{uuid.uuid4().hex[:16]}"


def course_prefix(course_id: int) -> str | None:
    """ПРЕФИКС КАТАЛОГА КУРСА В БАКЕ"""

    if not _is_safe_id(course_id):
        return None

    return f"{course_id}/"


def module_prefix(course_id: int, module_id: int) -> str | None:
    """ПРЕФИКС КАТАЛОГА МОДУЛЯ В БАКЕ"""

    if not _is_safe_id(course_id) or not _is_safe_id(module_id):
        return None

    return f"{course_id}/{module_id}/"


def media_prefix(course_id: int) -> str | None:
    """ПРЕФИКС КАТАЛОГА МЕДИАФАЙЛОВ КУРСА"""

    prefix = course_prefix(course_id)

    if prefix is None:
        return None

    return f"{prefix}{MEDIA_DIR_NAME}/"


def lesson_content_path(
        course_id: int,
        module_id: int,
        lesson_id: int,
) -> str | None:
    """ПУТЬ К MARKDOWN УРОКА В БАКЕ"""

    if not _is_safe_id(course_id) \
            or not _is_safe_id(module_id) \
            or not _is_safe_id(lesson_id):
        return None

    return f"{course_id}/{module_id}/{lesson_id}{MARKDOWN_EXTENSION}"


def module_content_path(course_id: int, module_id: int) -> str | None:
    """ПУТЬ К ВВОДНОМУ ТЕКСТУ МОДУЛЯ"""

    prefix = module_prefix(course_id=course_id, module_id=module_id)

    if prefix is None:
        return None

    return f"{prefix}{CONTENT_FILE_NAME}"


def course_content_path(course_id: int) -> str | None:
    """ПУТЬ К ВВОДНОМУ ТЕКСТУ КУРСА"""

    prefix = course_prefix(course_id)

    if prefix is None:
        return None

    return f"{prefix}{CONTENT_FILE_NAME}"


def media_object_key(
        course_id: int,
        media_key: str,
        extension: str,
) -> str | None:
    """КЛЮЧ ОБЪЕКТА МЕДИАФАЙЛА В БАКЕ

    Идентификатор приходит с сервера, но проверяется на всякий случай:
    в ключ объекта не должно попасть ничего, кроме безопасных символов.
    """

    prefix = media_prefix(course_id)

    if prefix is None:
        return None

    if not is_safe_media_key(media_key):
        return None

    if not extension.startswith(".") or not extension[1:].isalnum():
        return None

    return f"{prefix}{media_key}{extension}"


def course_cover_object_key(course_id: int) -> str | None:
    """КЛЮЧ ОБЪЕКТА ОБЛОЖКИ КУРСА В БАКЕ"""

    prefix = course_prefix(course_id)

    if prefix is None:
        return None

    return f"{prefix}{COVER_FILE_NAME}"
