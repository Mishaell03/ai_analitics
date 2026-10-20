"""ОБРАБОТЧИКИ КАСТОМНЫХ БЛОКОВ MARKDOWN

Кастомный блок — это фрагмент урока, который решается отдельно
от обычного Markdown: тест, видео, задание с кодом.

Чтобы добавить новый тип блока, достаточно:

    1. реализовать CustomBlockHandler;
    2. зарегистрировать обработчик в реестре.

Пока собственных обработчиков нет, любой тип блока разбирается
заглушкой и отдаётся клиенту как есть.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.core.markdown.models import CustomBlock


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
