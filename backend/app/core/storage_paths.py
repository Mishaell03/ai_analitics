"""ПРАВИЛА РАСКЛАДКИ ФАЙЛОВ В MINIO

Единое место, где описано, как лежат файлы курса в баках:

    lesson-content/
        {course_slug}/{module_id}/{lesson_id}.md   — Markdown урока
        {course_slug}/{module_id}/assets/...        — медиафайлы модуля

Пути строятся только по проверенным данным (slug из БД, числовые id),
поэтому в них не может оказаться выход за пределы бака.
"""

import re

# бак с контентом уроков
LESSON_CONTENT_BUCKET = "lesson-content"

# каталог медиафайлов внутри модуля
ASSETS_DIR_NAME = "assets"

# расширение файла с Markdown урока
MARKDOWN_EXTENSION = ".md"

# slug курса используется как часть пути, поэтому в нём допустимы
# только буквы, цифры, дефис и подчёркивание
_SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")


def is_safe_slug(course_slug: str) -> bool:
    """БЕЗОПАСЕН ЛИ SLUG ДЛЯ ИСПОЛЬЗОВАНИЯ В ПУТИ"""

    return bool(_SAFE_SLUG_RE.fullmatch(course_slug or ""))


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
