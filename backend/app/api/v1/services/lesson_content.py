"""СЕРВИС ДОСТУПА К СОДЕРЖИМОМУ УРОКА

Метаданные урока (название, описание, связи) лежат в БД, а сам
Markdown — в MinIO. Сервис проверяет доступ пользователя к курсу,
читает файл урока и отдаёт очищенное содержимое.
"""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import (
    CustomBlockResponse,
    LessonAssetResponse,
    LessonContentResponse,
    LessonInfo,
)
from app.api.v1.services.courses import BaseCoursesService
from app.core.config import settings
from app.core.markdown import MarkdownParser
from app.core.minio_url import minio_storage
from app.core.storage_paths import COURSE_CONTENT_BUCKET, lesson_content_path
from app.models.courses import Lesson


class LessonContentService(BaseCoursesService):
    """ЧИТАЕТ СОДЕРЖИМОЕ УРОКА ИЗ MINIO

    Наследует от BaseCoursesService проверки доступа к курсу,
    модулю и уроку: они одинаковы для списков и для содержимого.
    """

    def __init__(
            self,
            db: AsyncSession,
            parser: MarkdownParser | None = None,
    ):
        super().__init__(db)

        self._parser = parser or MarkdownParser()

    async def get_lesson_content(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
            is_admin: bool = False,
    ) -> LessonContentResponse:
        """СОДЕРЖИМОЕ УРОКА ВМЕСТЕ С МЕТАДАННЫМИ"""

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        module = await self._get_module(
            request=request,
            course=course,
            module_id=module_id,
            error=error,
        )

        lesson = await self._get_lesson(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        # содержимое урока доступно только записавшимся на курс,
        # администраторам доступно всегда
        if not is_enrolled and not is_admin:
            await self._raise(
                request=request,
                code="COURSE_ACCESS_REQUIRED",
                error=error,
            )

        return await self._read_content(
            request=request,
            lesson=lesson,
            course_id=course.course_id,
            error=error,
        )

    async def get_lesson_content_admin(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> LessonContentResponse:
        """СОДЕРЖИМОЕ УРОКА ДЛЯ АДМИНКИ

        Админ открывает любой урок, включая черновики: проверять
        урок нужно до публикации. Содержимое отдаётся очищенным,
        как и пользователю.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        # модуль должен принадлежать курсу
        if module.course_id != course.course_id:
            await self._raise(
                request=request,
                code="MODULE_NOT_FOUND",
                error=error,
            )

        lesson = await self._get_lesson_admin(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        return await self._read_content(
            request=request,
            lesson=lesson,
            course_id=course.course_id,
            error=error,
        )

    async def _read_content(
            self,
            request: Request,
            lesson: Lesson,
            course_id: int,
            error: dict,
    ) -> LessonContentResponse:
        """ЧИТАЕТ И ОЧИЩАЕТ MARKDOWN УРОКА

        Общая часть для пользователя и админа: набор правил очистки
        не должен зависеть от того, кто запросил урок.
        """

        file_path = lesson_content_path(
            course_id=course_id,
            module_id=lesson.module_id,
            lesson_id=lesson.lesson_id,
        )

        if file_path is None:
            # id нельзя использовать как часть пути
            await self._raise(
                request=request,
                code="LESSON_CONTENT_NOT_FOUND",
                error=error,
            )

        raw_content = await minio_storage.get_text(
            file_path=file_path,
            bucket=COURSE_CONTENT_BUCKET,
            max_bytes=settings.max_text_file_size,
        )

        if raw_content is None:
            await self._raise(
                request=request,
                code="LESSON_CONTENT_NOT_FOUND",
                error=error,
            )

        parsed = self._parser.parse(raw_content)

        content_url = await minio_storage.get_url(
            file_path=file_path,
            bucket=COURSE_CONTENT_BUCKET,
            expires=settings.content_url_ttl,
        )

        return LessonContentResponse(
            lesson=LessonInfo(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                description=lesson.description,
                position=lesson.position,
                content_url=content_url,
            ),
            content=parsed.content,
            content_type="markdown",
            custom_blocks=[
                CustomBlockResponse(
                    type=block.type,
                    content=block.content,
                    implemented=block.implemented,
                    data=block.data,
                )
                for block in parsed.custom_blocks
            ],
            assets=[
                LessonAssetResponse(
                    asset_id=asset.asset_id,
                    kind=asset.kind,
                    alt=asset.alt,
                    url=asset.url,
                )
                for asset in parsed.assets
            ],
        )
