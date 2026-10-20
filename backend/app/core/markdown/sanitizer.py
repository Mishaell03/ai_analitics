"""ОЧИСТКА MARKDOWN ПЕРЕД ОТДАЧЕЙ КЛИЕНТУ

Markdown приходит из MinIO, поэтому к нему нельзя относиться
как к доверенному тексту. Очистка убирает:

    * сырой HTML (включая опасные элементы вместе с содержимым);
    * ссылки с неизвестными и опасными протоколами
      (javascript:, data:, vbscript: и т. п.).

Содержимое блоков кода не трогается: там HTML может быть частью
примера, а протокол внутри кода ни на что не влияет.
"""

import re

# протоколы, которые разрешено отдавать клиенту
SAFE_URL_SCHEMES = frozenset({
    "http",
    "https",
    "mailto",
    "tel",
})

# элементы, которые вырезаются вместе со своим содержимым
_DANGEROUS_ELEMENTS = (
    "script",
    "style",
    "iframe",
    "object",
    "embed",
    "form",
    "svg",
    "math",
    "link",
    "meta",
    "base",
)

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_DANGEROUS_ELEMENT_RE = re.compile(
    r"<\s*(?P<tag>" + "|".join(_DANGEROUS_ELEMENTS) + r")\b[^>]*>.*?<\s*/\s*(?P=tag)\s*>",
    re.IGNORECASE | re.DOTALL,
)

_HTML_TAG_RE = re.compile(
    r"</?[a-zA-Z][a-zA-Z0-9-]*(?:\s[^<>]*?)?/?>|<\?[^<>]*\?>",
    re.DOTALL,
)

_INLINE_CODE_RE = re.compile(r"(?P<ticks>`+)(?P<code>.+?)(?P=ticks)", re.DOTALL)

_LINK_DESTINATION_RE = re.compile(
    r"\]\(\s*(?P<dest>[^()\s]*(?:\([^()]*\)[^()\s]*)*)"
    r"(?P<title>\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))?\s*\)",
)

_LINK_DEFINITION_RE = re.compile(
    r"^(?P<indent>\s*)\[(?P<label>[^\]]+)\]:(?P<space>\s*)(?P<dest>\S+)(?P<rest>.*)$",
)


def is_safe_url(url: str) -> bool:
    """БЕЗОПАСНА ЛИ ССЫЛКА

    Относительные ссылки и ссылки с разрешённым протоколом безопасны,
    всё остальное (javascript:, data:, vbscript:, ...) — нет.
    """

    if not url:
        return True

    cleaned = url.strip().strip("<>")

    if not cleaned:
        return True

    scheme, separator, _ = cleaned.partition(":")

    if not separator:
        return True

    return scheme.lower() in SAFE_URL_SCHEMES


class MarkdownSanitizer:
    """Убирает из Markdown всё, что нельзя безопасно отдать клиенту"""

    def sanitize(
            self,
            source: str,
            protected_lines: set[int] | None = None,
            removed_lines: set[int] | None = None,
    ) -> str:
        """ОЧИЩАЕТ ИСХОДНЫЙ MARKDOWN

        protected_lines — строки внутри блоков кода, их не трогаем;
        removed_lines — строки сырого HTML, их вырезаем целиком.
        """

        protected_lines = protected_lines or set()
        removed_lines = removed_lines or set()

        if not source:
            return ""

        clean_lines = []

        for index, line in enumerate(source.splitlines()):
            if index in removed_lines:
                continue

            if index in protected_lines:
                clean_lines.append(line)
                continue

            clean_lines.append(self._sanitize_line(line))

        content = "\n".join(clean_lines)

        # перевод строки в конце файла сохраняем
        if content and source.endswith("\n"):
            content += "\n"

        return content

    def _sanitize_line(self, line: str) -> str:
        """ОЧИЩАЕТ ОДНУ СТРОКУ, СОХРАНЯЯ ИНЛАЙН-КОД"""

        result = []

        position = 0

        for match in _INLINE_CODE_RE.finditer(line):
            result.append(self._sanitize_text(line[position:match.start()]))
            result.append(match.group(0))
            position = match.end()

        result.append(self._sanitize_text(line[position:]))

        return "".join(result)

    def _sanitize_text(self, text: str) -> str:
        """ОЧИЩАЕТ ТЕКСТ ВНУТРИ СТРОКИ"""

        if not text:
            return text

        text = _COMMENT_RE.sub("", text)
        text = _DANGEROUS_ELEMENT_RE.sub("", text)
        text = _HTML_TAG_RE.sub("", text)
        text = _LINK_DESTINATION_RE.sub(self._replace_destination, text)
        text = _LINK_DEFINITION_RE.sub(self._replace_definition, text)

        return text

    @staticmethod
    def _replace_destination(match: re.Match) -> str:
        """УБИРАЕТ ОПАСНЫЙ АДРЕС ССЫЛКИ, СОХРАНЯЯ САМУ ССЫЛКУ"""

        destination = match.group("dest")

        if is_safe_url(destination):
            return match.group(0)

        title = match.group("title") or ""

        return f"]({title})"

    @staticmethod
    def _replace_definition(match: re.Match) -> str:
        """УБИРАЕТ ОПАСНЫЙ АДРЕС ОПРЕДЕЛЕНИЯ ССЫЛКИ"""

        destination = match.group("dest")

        if is_safe_url(destination):
            return match.group(0)

        return (
            f"{match.group('indent')}[{match.group('label')}]:"
            f"{match.group('space')}{match.group('rest')}"
        )
