"""СЕРВИС ОБЛОЖКИ КУРСА

Обложка — это изображение в приватном MinIO и запись в БД с
метаданными. Presigned URL в базе не хранится: он выдаётся клиенту
по запросу и живёт недолго.

Замена обложки безопасна: новый файл сначала загружается в хранилище,
потом в базе меняется ссылка на него, и только после этого удаляется
старый файл. Если что-то сломалось на середине, у курса останется
рабочая обложка.
"""

import logging
from io import BytesIO

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.media import CourseImageResponse
from app.api.v1.services.courses import BaseCoursesService
from app.core.config import settings
from app.core.minio_url import minio_storage
from app.core.storage_paths import (
    MEDIA_BUCKET,
    course_cover_object_key,
    generate_file_id,
)
from app.models.media import CourseImage
from app.utils.img_convertor import ImageValidationError, image_convertor


class CourseImageService(BaseCoursesService):
    """УПРАВЛЕНИЕ ОБЛОЖКОЙ КУРСА"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def upload_image(
            self,
            request: Request,
            course_slug: str,
            file,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> CourseImageResponse:
        """ЗАГРУЖАЕТ (ИЛИ ЗАМЕНЯЕТ) ОБЛОЖКУ КУРСА"""

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

        try:
            data = await self._read_image(file)

            image = await image_convertor.to_webp(
                data=data,
                content_type=file.content_type,
            )

        except ImageValidationError as error_:
            await self._raise(
                request=request,
                code=error_.code,
                error=error,
            )

        file_id = generate_file_id()

        object_key = course_cover_object_key(
            course_id=course.course_id,
            file_id=file_id,
        )

        if object_key is None:
            await self._raise(
                request=request,
                code="MEDIA_FILE_CORRUPTED",
                error=error,
            )

        # старый файл удаляем только после того, как новый записан в БД
        old_image = await self._get_image_row(course_id=course.course_id)

        # ключ старого файла запоминаем до изменения записи в базе
        old_object_key = old_image.object_key if old_image is not None else None

        await minio_storage.put_stream(
            data=BytesIO(image.content),
            length=image.size_bytes,
            bucket=MEDIA_BUCKET,
            file_path=object_key,
            content_type=image.content_type,
        )

        try:
            if old_image is None:
                new_image = CourseImage(
                    course_id=course.course_id,
                    file_id=file_id,
                    object_key=object_key,
                    content_type=image.content_type,
                    size_bytes=image.size_bytes,
                    width=image.width,
                    height=image.height,
                )

                self.db.add(new_image)

            else:
                new_image = old_image

                new_image.file_id = file_id
                new_image.object_key = object_key
                new_image.content_type = image.content_type
                new_image.size_bytes = image.size_bytes
                new_image.width = image.width
                new_image.height = image.height

            await self.db.commit()
            await self.db.refresh(new_image)

        except IntegrityError:
            await self.db.rollback()

            # файл уже загружен, но в базу не попал — убираем его
            await minio_storage.delete_file(
                file_path=object_key,
                bucket=MEDIA_BUCKET,
            )

            await self._raise(
                request=request,
                code="MEDIA_FILE_CORRUPTED",
                error=error,
            )

        if old_object_key is not None and old_object_key != object_key:
            await minio_storage.delete_file(
                file_path=old_object_key,
                bucket=MEDIA_BUCKET,
            )

        url = await minio_storage.get_url(
            file_path=new_image.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        return self._to_response(image=new_image, url=url)

    async def get_image(
            self,
            request: Request,
            course_slug: str,
            language: str,
            is_admin: bool = False,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> CourseImageResponse:
        """ОБЛОЖКА КУРСА СО ССЫЛКОЙ

        Обложка — часть карточки курса, поэтому она доступна всем,
        кому доступен сам курс. Ссылка короткоживущая и выдаётся
        только после проверки доступа к курсу.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        if is_admin:
            course = await self._get_course_admin(
                request=request,
                course_slug=course_slug,
                error=error,
            )

        else:
            # обычному пользователю доступен только опубликованный курс
            course = await self._get_course(
                request=request,
                course_slug=course_slug,
                error=error,
            )

        image = await self._get_image_row(course_id=course.course_id)

        if image is None:
            await self._raise(
                request=request,
                code="COURSE_IMAGE_NOT_FOUND",
                error=error,
            )

        url = await minio_storage.get_url(
            file_path=image.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        return self._to_response(image=image, url=url)

    async def delete_image(
            self,
            request: Request,
            course_slug: str,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> CourseImageResponse:
        """УДАЛЯЕТ ОБЛОЖКУ КУРСА"""

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

        image = await self._get_image_row(course_id=course.course_id)

        if image is None:
            await self._raise(
                request=request,
                code="COURSE_IMAGE_NOT_FOUND",
                error=error,
            )

        object_key = image.object_key
        file_id = image.file_id

        await self.db.delete(image)
        await self.db.commit()

        await minio_storage.delete_file(
            file_path=object_key,
            bucket=MEDIA_BUCKET,
        )

        logging.info("course image deleted: course=%s file=%s", course.course_id, file_id)

        return CourseImageResponse(
            file_id=file_id,
            course_id=course.course_id,
            content_type="image/webp",
            size_bytes=0,
            width=0,
            height=0,
            created_at=image.created_at,
            updated_at=image.updated_at,
            url=None,
        )

    async def get_covers_map(
            self,
            course_ids: list[int],
    ) -> dict[int, CourseImage]:
        """ОБЛОЖКИ КУРСОВ ОДНИМ ЗАПРОСОМ

        Нужно, чтобы не делать по запросу на каждый курс в списке.
        """

        if not course_ids:
            return {}

        result = await self.db.execute(
            select(CourseImage).where(CourseImage.course_id.in_(course_ids))
        )

        return {image.course_id: image for image in result.scalars().all()}

    async def _get_image_row(self, course_id: int) -> CourseImage | None:
        """ЗАПИСЬ ОБЛОЖКИ КУРСА ИЛИ None"""

        result = await self.db.execute(
            select(CourseImage).where(CourseImage.course_id == course_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def _read_image(file) -> bytes:
        """ЧИТАЕТ ФАЙЛ С ОГРАНИЧЕНИЕМ ПО РАЗМЕРУ

        Файл целиком попадает в память, но не больше разрешённого
        лимита: файл читается с ограничением.
        """

        data = await file.read(settings.media_max_image_size + 1)

        if len(data) > settings.media_max_image_size:
            raise ImageValidationError(
                code="MEDIA_FILE_TOO_LARGE",
                message="Файл изображения больше допустимого размера",
            )

        return data

    @staticmethod
    def _to_response(image: CourseImage, url: str | None) -> CourseImageResponse:
        """ОТВЕТ API С МЕТАДАННЫМИ ОБЛОЖКИ"""

        return CourseImageResponse(
            file_id=image.file_id,
            course_id=image.course_id,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            width=image.width,
            height=image.height,
            created_at=image.created_at,
            updated_at=image.updated_at,
            url=url,
        )
