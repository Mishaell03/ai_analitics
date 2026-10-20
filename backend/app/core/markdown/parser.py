"""РАЗБОР MARKDOWN УРОКА

Задача модуля — разобрать пришедший из MinIO Markdown на части,
которые нужны клиенту:

    * очищенный текст урока;
    * кастомные блоки (тесты, видео, задания) — заготовка под них;
    * ссылки на медиафайлы, упомянутые в тексте.
"""

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.core.markdown.custom_blocks import CustomBlockRegistry
from app.core.markdown.models import CustomBlock, LessonAsset, ParsedMarkdown
from app.core.markdown.sanitizer import MarkdownSanitizer
from app.core.storage_paths import ASSETS_DIR_NAME

# разметка кастомного блока: :::тип ... :::
_CUSTOM_BLOCK_OPEN_RE = re.compile(r"^:::\s*(?P<type>[a-zA-Z][a-zA-Z0-9_-]*)\s*$")
_CUSTOM_BLOCK_CLOSE_RE = re.compile(r"^:::\s*$")

# типы блоков кода, содержимое которых нельзя чистить
_CODE_TOKEN_TYPES = frozenset({
    "fence",
    "code_block",
})

_IMAGE_EXTENSIONS = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".avif",
    ".bmp",
})

_VIDEO_EXTENSIONS = frozenset({
    ".mp4",
    ".webm",
    ".mov",
    ".mkv",
    ".avi",
})


class MarkdownParser:
    """РАЗБИРАЕТ MARKDOWN УРОКА НА СОСТАВНЫЕ ЧАСТИ"""

    def __init__(
            self,
            sanitizer: MarkdownSanitizer | None = None,
            custom_blocks: CustomBlockRegistry | None = None,
    ):
        self._sanitizer = sanitizer or MarkdownSanitizer()
        self._custom_blocks = custom_blocks or CustomBlockRegistry()
        self._markdown = MarkdownIt("commonmark").enable("table")

    def parse(self, source: str) -> ParsedMarkdown:
        """РАЗБИРАЕТ ИСХОДНЫЙ MARKDOWN УРОКА"""

        if not source:
            return ParsedMarkdown(content="")

        tokens = self._markdown.parse(source)

        protected_lines, removed_lines = self._collect_line_ranges(tokens)

        content = self._sanitizer.sanitize(
            source=source,
            protected_lines=protected_lines,
            removed_lines=removed_lines,
        )

        return ParsedMarkdown(
            content=content,
            custom_blocks=self._extract_custom_blocks(content),
            assets=self._extract_assets(tokens),
        )

    @staticmethod
    def _collect_line_ranges(tokens: list[Token]) -> tuple[set[int], set[int]]:
        """ОПРЕДЕЛЯЕТ СТРОКИ КОДА И СЫРОГО HTML

        Строки кода не чистятся, строки HTML вырезаются целиком.
        """

        protected_lines: set[int] = set()
        removed_lines: set[int] = set()

        for token in tokens:
            if not token.map:
                continue

            start, end = token.map

            if token.type in _CODE_TOKEN_TYPES:
                protected_lines.update(range(start, end))

            elif token.type == "html_block":
                removed_lines.update(range(start, end))

        return protected_lines, removed_lines

    def _extract_custom_blocks(self, content: str) -> tuple[CustomBlock, ...]:
        """ВЫДЕЛЯЕТ КАСТОМНЫЕ БЛОКИ ИЗ ТЕКСТА УРОКА"""

        blocks: list[CustomBlock] = []

        lines = content.splitlines()

        index = 0

        while index < len(lines):
            open_match = _CUSTOM_BLOCK_OPEN_RE.match(lines[index])

            if open_match is None:
                index += 1
                continue

            block_type = open_match.group("type")
            block_lines: list[str] = []

            index += 1
            closed = False

            while index < len(lines):
                if _CUSTOM_BLOCK_CLOSE_RE.match(lines[index]):
                    closed = True
                    index += 1
                    break

                block_lines.append(lines[index])
                index += 1

            # незакрытый блок — обычный текст, а не блок
            if not closed:
                continue

            blocks.append(
                self._custom_blocks.parse(
                    block_type=block_type,
                    content="\n".join(block_lines).strip(),
                )
            )

        return tuple(blocks)

    def _extract_assets(self, tokens: list[Token]) -> tuple[LessonAsset, ...]:
        """СОБИРАЕТ УПОМЯНУТЫЕ В УРОКЕ МЕДИАФАЙЛЫ"""

        assets: list[LessonAsset] = []
        known_ids: set[str] = set()

        for token in self._walk(tokens):
            if token.type == "image":
                source = token.attrGet("src") or ""
                alt = token.content or token.attrGet("alt") or None

            elif token.type == "link_open":
                source = token.attrGet("href") or ""
                alt = None

            else:
                continue

            asset_id = self._get_asset_id(source)

            if asset_id is None or asset_id in known_ids:
                continue

            known_ids.add(asset_id)

            assets.append(
                LessonAsset(
                    asset_id=asset_id,
                    kind=self._get_asset_kind(asset_id),
                    alt=alt,
                )
            )

        return tuple(assets)

    @classmethod
    def _walk(cls, tokens: list[Token]):
        """ПЕРЕБИРАЕТ ТОКЕНЫ ВМЕСТЕ С ВЛОЖЕННЫМИ"""

        for token in tokens:
            yield token

            if token.children:
                yield from cls._walk(token.children)

    @staticmethod
    def _get_asset_id(source: str) -> str | None:
        """ИДЕНТИФИКАТОР МЕДИАФАЙЛА ИЗ ССЫЛКИ В MARKDOWN

        Поддерживаются ссылки вида assets/schema.png и schema.png.
        """

        if not source:
            return None

        assets_prefix = f"{ASSETS_DIR_NAME}/"

        if source.startswith(assets_prefix):
            asset_id = source[len(assets_prefix):]

        elif "/" not in source and ":" not in source and "." in source:
            asset_id = source

        else:
            return None

        if not asset_id or asset_id.startswith("/") or ".." in asset_id:
            return None

        return asset_id

    @staticmethod
    def _get_asset_kind(asset_id: str) -> str:
        """ТИП МЕДИАФАЙЛА ПО РАСШИРЕНИЮ"""

        _, _, extension = asset_id.rpartition(".")

        extension = f".{extension.lower()}"

        if extension in _IMAGE_EXTENSIONS:
            return "image"

        if extension in _VIDEO_EXTENSIONS:
            return "video"

        return "file"
