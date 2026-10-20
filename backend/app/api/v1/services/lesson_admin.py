"""СЕРВИС СОЗДАНИЯ УРОКОВ (ADMIN)

Урок создаётся в два шага:

    1. админ создаёт урок в БД и получает ссылку для загрузки;
    2. клиент отправляет Markdown урока в MinIO по этой ссылке.

Ограничение по размеру файла проверяет сам MinIO: политика presigned POST
содержит content-length-range, поэтому файл больше лимита будет отклонён
с ошибкой на стороне хранилища.
"""

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.v1.schemas.courses import (
    LessonAdminResponse,
    LessonCreateRequest,
    LessonUploadResponse,
)
from app.api.v1.services.courses import BaseCoursesService
from app.core.config import settings
from app.core.minio_url import minio_storage
from app.core.storage_paths import LESSON_CONTENT_BUCKET, lesson_content_path
from app.models.courses import Lesson

# урок — это Markdown, поэтому и тип файла такой же
MARKDOWN_CONTENT_TYPE = "text/markdown"


class LessonAdminService(BaseCoursesService):
    """СОЗДАЁТ УРОКИ И ВЫДАЁТ ССЫЛКИ НА ЗАГРУЗКУ МАРKDOWN"""

    async def create_lesson(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            data: LessonCreateRequest,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> LessonAdminResponse:
        """СОЗДАЁТ УРОК И ССЫЛКУ НА ЗАГРУЗКУ ЕГО MARKDOWN"""

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

        position = data.position

        if position is None:
            result = await self.db.execute(
                select(func.max(Lesson.position)).where(Lesson.module_id == module.module_id)
            )

            max_position = result.scalar_one_or_none()

            position = (max_position or 0) + 1

        is_published = data.is_published

        if is_published is None:
            is_published = data.is_active if data.is_active is not None else False

        lesson = Lesson(
            module_id=module.module_id,
            title=data.title,
            description=data.description,
            position=position,
            is_published=is_published,
        )

        self.db.add(lesson)

        try:
            # id урока нужен для пути файла, поэтому сначала flush,
            # а не commit: если ссылка не построится, урок не останется в базе
            await self.db.flush()

            upload = await self._build_upload(
                request=request,
                course_slug=course.slug,
                module_id=module.module_id,
                lesson_id=lesson.lesson_id,
                error=error,
            )

            await self.db.commit()
            await self.db.refresh(lesson)

        except IntegrityError:
            # занятая позиция в модуле или другая конфликтующая запись
            await self.db.rollback()

            await self._raise(
                request=request,
                code="REGISTRATION_FAILED",
                error=error,
            )

        except HTTPException:
            await self.db.rollback()

            raise

        return LessonAdminResponse(
            success=True,
            lesson_id=lesson.lesson_id,
            id=lesson.lesson_id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            position=lesson.position,
            is_published=lesson.is_published,
            is_active=lesson.is_published,
            has_content=False,
            upload=upload,
        )

    async def get_lesson_upload_url(
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
    ) -> LessonUploadResponse:
        """НОВАЯ ССЫЛКА НА ЗАГРУЗКУ MARKDOWN УРОКА

        Ссылка из ответа на создание живёт недолго, поэтому для
        перезаписи файла её можно запросить заново.
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

        return await self._build_upload(
            request=request,
            course_slug=course.slug,
            module_id=module.module_id,
            lesson_id=lesson.lesson_id,
            error=error,
        )

    async def _build_upload(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            error: dict,
    ) -> LessonUploadResponse:
        """ССЫЛКА НА ЗАГРУЗКУ ФАЙЛА УРОКА В MINIO"""

        file_path = lesson_content_path(
            course_slug=course_slug,
            module_id=module_id,
            lesson_id=lesson_id,
        )

        if file_path is None:
            # slug курса нельзя использовать как часть пути
            await self._raise(
                request=request,
                code="INVALID_COURSE_SLUG",
                error=error,
            )

        max_size = settings.lesson_content_max_upload_size

        upload = await minio_storage.get_upload_url(
            bucket=LESSON_CONTENT_BUCKET,
            file_path=file_path,
            max_size=max_size,
            content_type=MARKDOWN_CONTENT_TYPE,
        )

        return LessonUploadResponse(
            url=upload["url"],
            fields=upload["fields"],
            file_path=file_path,
            max_size=max_size,
            expires_in=settings.upload_url_ttl,
        )
