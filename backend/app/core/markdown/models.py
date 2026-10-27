"""МОДЕЛИ ДОМЕНА MARKDOWN УРОКА

Простые неизменяемые объекты: ядро не зависит от транспортных
схем API, а сервис отдаёт их наружу через pydantic-схемы.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CustomBlock:
    """КАСТОМНЫЙ БЛОК ВНУТРИ MARKDOWN УРОКА

    Блок выделяется разметкой:

        :::video
        https://example.com/video.mp4
        :::

    Логика блоков (тесты, видео, задания с кодом) появится позже,
    поэтому заполненный блок отдаётся как есть. Разобранные данные
    блока (например, идентификатор задания) кладутся в data.
    """

    type: str
    content: str
    implemented: bool = False
    data: dict | None = None


@dataclass(frozen=True)
class LessonAsset:
    """ССЫЛКА НА МЕДИАФАЙЛ УРОКА

    В Markdown указывается идентификатор файла, а не ссылка:

        ![схема работы](assets/schema.png)

    Идентификатор потом превращается в presigned URL
    (см. следующий этап — выдача медиафайлов).
    """

    asset_id: str
    kind: str = "image"
    alt: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class ParsedMarkdown:
    """РЕЗУЛЬТАТ РАЗБОРА MARKDOWN УРОКА

    content — очищенный Markdown, готовый к отображению;
    custom_blocks и assets — индексы по этому же тексту.
    """

    content: str
    custom_blocks: tuple[CustomBlock, ...] = field(default_factory=tuple)
    assets: tuple[LessonAsset, ...] = field(default_factory=tuple)
