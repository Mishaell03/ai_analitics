"""ОБРАБОТЧИКИ КАСТОМНЫХ БЛОКОВ MARKDOWN

Кастомный блок — это фрагмент урока, который решается отдельно
от обычного Markdown: тест, видео, задание с кодом.

Чтобы добавить новый тип блока, достаточно:

    1. реализовать CustomBlockHandler;
    2. зарегистрировать обработчик в реестре.

Пока собственных обработчиков нет, любой тип блока разбирается
заглушкой и отдаётся как есть.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.core.markdown.models import CustomBlock

# идентификатор задания задаётся первой строкой содержимого блока:
#
#     :::test
#     id: python-variables
#     Текст задания
#     :::
_EXERCISE_ID_LINE_RE = re.compile(
    r"^id:\s*(?P<exercise_id>[A-Za-z0-9_-]{1,64})\s*$",
    re.IGNORECASE,
)

_OPTION_LINE_RE = re.compile(
    r"^\s*[-*+]\s+(?:\[(?P<multiple>[ xXхХ])\]|\((?P<single>[ xXхХ])\))\s*.*$"
)


def split_exercise_header(content: str) -> tuple[str | None, str]:
    """ОТДЕЛЯЕТ ИДЕНТИФИКАТОР ЗАДАНИЯ ОТ ТЕКСТА

    Возвращает идентификатор задания (None, если его нет) и текст
    задания без строки с идентификатором.
    """

    lines = content.splitlines()

    if not lines:
        return None, content

    match = _EXERCISE_ID_LINE_RE.match(lines[0])

    if match is None:
        return None, content

    return match.group("exercise_id"), "\n".join(lines[1:]).strip()


class CustomBlockHandler(ABC):
    """ОБРАБОТЧИК ОДНОГО ТИПА КАСТОМНОГО БЛОКА"""

    # тип блока в разметке (:::video, :::test, ...)
    type: str = ""

    @abstractmethod
    def parse(self, content: str) -> CustomBlock:
        """РАЗБИРАЕТ СОДЕРЖИМОЕ БЛОКА"""


class PlaceholderCustomBlockHandler(CustomBlockHandler):
    """ЗАГЛУШКА ДЛЯ ТИПОВ БЛОКОВ БЕЗ СОБСТВЕННОГО ОБРАБОТЧИКА

    Содержимое блока не интерпретируется: клиент получает его
    в исходном виде и решает, что с ним делать.
    """

    def __init__(self, type: str):
        self.type = type

    def parse(self, content: str) -> CustomBlock:
        return CustomBlock(
            type=self.type,
            content=content,
            implemented=False,
        )


class TestBlockHandler(CustomBlockHandler):
    """ЗАДАНИЕ УРОКА

    Задание записывается в Markdown так:

        :::test
        id: python-variables
        Текст задания
        :::

    Идентификатор связывает задание с правильным ответом, который
    хранится в базе. Само задание (вопрос, варианты ответа) пока
    не разбирается: клиент получает его как есть.
    """

    type = "test"

    def parse(self, content: str) -> CustomBlock:
        exercise_id, body = split_exercise_header(content)
        option_types = set()
        for line in body.splitlines():
            option = _OPTION_LINE_RE.match(line)
            if option is None:
                continue
            single = option.group("single") is not None
            option_types.add(single)
            if (option.group("single") if single else option.group("multiple")).strip():
                raise ValueError("Correct answers belong in the database, not Markdown")
        if len(option_types) > 1:
            raise ValueError("Do not mix single and multiple choice options")
        data = {"exercise_id": exercise_id, "body": body}
        # Язык задаёт автор урока, а не запрос ученика. Только явный заголовок.
        lines = body.splitlines()
        if exercise_id and lines and lines[0] in {"language: python", "language: sql"}:
            data["language"] = lines[0].removeprefix("language: ")
            data["body"] = "\n".join(lines[1:]).strip()

        return CustomBlock(
            type=self.type,
            content=content,
            implemented=False,
            data=data,
        )


class CodeBlockHandler(CustomBlockHandler):
    """В Markdown допустим только язык и идентификатор, не решение."""

    type = "code"

    def parse(self, content: str) -> CustomBlock:
        lines = content.splitlines()
        language = lines[0].removeprefix("language: ") if lines else None
        exercise_id, body = split_exercise_header("\n".join(lines[1:]))
        if language not in {"sql", "python"} or not exercise_id or body or exercise_id == "reference":
            raise ValueError("Invalid code directive: use :::code sql/python, id: identifier, :::")
        return CustomBlock(type=self.type, content=f"id: {exercise_id}", implemented=True,
                           data={"exercise_id": exercise_id, "language": language, "body": ""})


class CustomBlockRegistry:
    """РЕЕСТР ОБРАБОТЧИКОВ КАСТОМНЫХ БЛОКОВ"""

    def __init__(self, handlers: Iterable[CustomBlockHandler] | None = None):
        self._handlers: dict[str, CustomBlockHandler] = {}

        for handler in handlers or ():
            self.register(handler)

    def register(self, handler: CustomBlockHandler) -> None:
        """РЕГИСТРИРУЕТ ОБРАБОТЧИК ТИПА БЛОКА"""

        self._handlers[handler.type] = handler

    def parse(self, block_type: str, content: str) -> CustomBlock:
        """РАЗБИРАЕТ БЛОК НУЖНЫМ ОБРАБОТЧИКОМ

        Для незарегистрированных типов используется заглушка.
        """

        handler = self._handlers.get(block_type)

        if handler is None:
            handler = PlaceholderCustomBlockHandler(block_type)

        return handler.parse(content)


def default_custom_block_registry() -> CustomBlockRegistry:
    """РЕЕСТР СОБСТВЕННЫМИ ОБРАБОТЧИКАМИ"""

    return CustomBlockRegistry(handlers=[TestBlockHandler(), CodeBlockHandler()])
