"""СЕРВИС МЕДИАФАЙЛОВ УРОКА

Медиафайл — это отдельный объект в приватном MinIO и запись в БД:

    * изображение пережимается в WebP и чистится от метаданных;
    * видео сохраняется как есть, но проверяется, что это настоящий
      MP4 с кодеками H.264/AAC — такой файл играет во всех браузерах.

Видео не читается в память целиком: файл осматривается по структуре
контейнера и отдаётся в MinIO потоком.
"""

import logging
from io import BytesIO

from fastapi import Request
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.media import (
    MEDIA_KIND_IMAGE,
    MEDIA_KIND_VIDEO,
    MediaInfoResponse,
    MediaListResponse,
    MediaUrlResponse,
)
from app.api.v1.services.courses import BaseCoursesService
from app.core.config import settings
from app.core.minio_url import minio_storage
from app.core.pagination import get_pagination, get_total_pages
from app.core.storage_paths import (
    MEDIA_BUCKET,
    generate_media_key,
    media_object_key,
)
from app.models.media import LessonMedia, MediaFile
from app.utils.img_convertor import ImageValidationError, image_convertor
from app.utils.video_inspector import (
    AUDIO_CODEC_AAC,
    VIDEO_CODEC_H264,
    VideoValidationError,
    video_inspector,
)

# расширения, по которым определяется тип файла
_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"})
_VIDEO_EXTENSIONS = frozenset({".mp4"})

# кодек видео, который понимают браузеры
_REQUIRED_VIDEO_CODEC = VIDEO_CODEC_H264

# кодек аудио, который понимают браузеры
_REQUIRED_AUDIO_CODEC = AUDIO_CODEC_AAC


class LessonMediaService(BaseCoursesService):
    """УПРАВЛЕНИЕ МЕДИАФАЙЛАМИ УРОКА"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def upload_media(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            file,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaInfoResponse:
        """ЗАГРУЖАЕТ МЕДИАФАЙЛ УРОКА"""

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

        kind = await self._resolve_kind(request=request, file=file, error=error)

        media_key = generate_media_key()

        if kind == MEDIA_KIND_IMAGE:
            image = await self._prepare_image(request=request, file=file, error=error)

            object_key = media_object_key(
                course_id=course.course_id,
                media_key=media_key,
                extension=".webp",
            )

            content_type = image.content_type
            size_bytes = image.size_bytes
            width = image.width
            height = image.height
            duration_seconds = None
            video_codec = None
            audio_codec = None

            payload = BytesIO(image.content)

        else:
            video = await self._prepare_video(request=request, file=file, error=error)

            object_key = media_object_key(
                course_id=course.course_id,
                media_key=media_key,
                extension=".mp4",
            )

            content_type = "video/mp4"
            size_bytes = video.size_bytes
            width = video.width
            height = video.height
            duration_seconds = video.duration_seconds
            video_codec = video.video_codec
            audio_codec = video.audio_codec

            payload = video.payload

        if object_key is None:
            await self._raise(
                request=request,
                code="MEDIA_FILE_CORRUPTED",
                error=error,
            )

        await minio_storage.put_stream(
            data=payload,
            length=size_bytes,
            bucket=MEDIA_BUCKET,
            file_path=object_key,
            content_type=content_type,
        )

        media = MediaFile(
            media_key=media_key,
            course_id=course.course_id,
            object_key=object_key,
            kind=kind,
            content_type=content_type,
            size_bytes=size_bytes,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            video_codec=video_codec,
            audio_codec=audio_codec,
            original_name=self._get_original_name(file),
        )

        self.db.add(media)

        try:
            await self.db.flush()

            self.db.add(
                LessonMedia(
                    lesson_id=lesson.lesson_id,
                    media_id=media.media_id,
                )
            )

            await self.db.commit()
            await self.db.refresh(media)

        except IntegrityError:
            await self.db.rollback()

            # файл загружен, но в базу не попал — убираем его
            await minio_storage.delete_file(
                file_path=object_key,
                bucket=MEDIA_BUCKET,
            )

            await self._raise(
                request=request,
                code="MEDIA_FILE_CORRUPTED",
                error=error,
            )

        url = await minio_storage.get_url(
            file_path=media.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        return self._to_response(media=media, lesson_id=lesson.lesson_id, url=url)

    async def list_media(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            language: str,
            page: int = 1,
            page_size: int = 20,
            is_admin: bool = False,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaListResponse:
        """МЕДИАФАЙЛЫ УРОКА

        Обычному пользователю доступны только опубликованные уроки
        записанного им курса; админу — всё.
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

            module = await self._get_module_admin(
                request=request,
                module_id=module_id,
                error=error,
            )

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

        else:
            course = await self._get_course(
                request=request,
                course_slug=course_slug,
                error=error,
            )

            is_enrolled = await self._is_enrolled(
                user_id=user_id,
                course_id=course.course_id,
            )

            if not is_enrolled:
                await self._raise(
                    request=request,
                    code="COURSE_ACCESS_REQUIRED",
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

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        total_result = await self.db.execute(
            select(func.count(MediaFile.media_id))
            .join(LessonMedia, LessonMedia.media_id == MediaFile.media_id)
            .where(LessonMedia.lesson_id == lesson.lesson_id)
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        result = await self.db.execute(
            select(MediaFile)
            .join(LessonMedia, LessonMedia.media_id == MediaFile.media_id)
            .where(LessonMedia.lesson_id == lesson.lesson_id)
            .order_by(MediaFile.created_at, MediaFile.media_id)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        items = []

        for media in result.scalars().all():
            url = await minio_storage.get_url(
                file_path=media.object_key,
                bucket=MEDIA_BUCKET,
                expires=settings.media_url_ttl,
            )

            items.append(
                self._to_response(
                    media=media,
                    lesson_id=lesson.lesson_id,
                    url=url,
                )
            )

        return MediaListResponse(
            media=items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_media(
            self,
            request: Request,
            media_key: str,
            language: str,
            is_admin: bool = False,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaInfoResponse:
        """МЕТАДАННЫЕ МЕДИАФАЙЛА"""

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        media = await self._get_media_row(
            request=request,
            media_key=media_key,
            error=error,
        )

        await self._check_media_access(
            request=request,
            media=media,
            is_admin=is_admin,
            user_id=user_id,
            error=error,
        )

        url = await minio_storage.get_url(
            file_path=media.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        return self._to_response(media=media, lesson_id=None, url=url)

    async def get_media_url(
            self,
            request: Request,
            media_key: str,
            language: str,
            is_admin: bool = False,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaUrlResponse:
        """НОВАЯ ССЫЛКА НА ПРОСМОТР ФАЙЛА

        Ссылки короткоживущие, поэтому новую можно запросить в любой
        момент: доступ к файлу проверяется заново.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        media = await self._get_media_row(
            request=request,
            media_key=media_key,
            error=error,
        )

        await self._check_media_access(
            request=request,
            media=media,
            is_admin=is_admin,
            user_id=user_id,
            error=error,
        )

        url = await minio_storage.get_url(
            file_path=media.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        if url is None:
            await self._raise(
                request=request,
                code="MEDIA_FILE_NOT_FOUND",
                error=error,
            )

        return MediaUrlResponse(
            media_id=media.media_id,
            media_key=media.media_key,
            url=url,
            content_type=media.content_type,
            size_bytes=media.size_bytes,
            expires_in=settings.media_url_ttl,
        )

    async def attach_media(
            self,
            request: Request,
            lesson_id: int,
            media_key: str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaInfoResponse:
        """ПРИВЯЗЫВАЕТ СУЩЕСТВУЮЩИЙ ФАЙЛ К УРОКУ

        Один файл можно использовать в нескольких уроках курса:
        он загружается один раз, а ссылки на него добавляются отдельно.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        media = await self._get_media_row(
            request=request,
            media_key=media_key,
            error=error,
        )

        module = await self._get_lesson_module(
            request=request,
            lesson_id=lesson_id,
            error=error,
        )

        lesson = await self._get_lesson_admin(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        # файл должен принадлежать курсу урока
        if media.course_id != module.course_id:
            await self._raise(
                request=request,
                code="MEDIA_FILE_NOT_FOUND",
                error=error,
            )

        self.db.add(
            LessonMedia(
                lesson_id=lesson.lesson_id,
                media_id=media.media_id,
            )
        )

        try:
            await self.db.commit()

        except IntegrityError:
            # файл уже привязан к уроку
            await self.db.rollback()

        url = await minio_storage.get_url(
            file_path=media.object_key,
            bucket=MEDIA_BUCKET,
            expires=settings.media_url_ttl,
        )

        return self._to_response(media=media, lesson_id=lesson.lesson_id, url=url)

    async def delete_media(
            self,
            request: Request,
            media_key: str,
            lesson_id: int | None = None,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> MediaListResponse:
        """УДАЛЯЕТ МЕДИАФАЙЛ

        Если файл указан в нескольких уроках, из урока он только
        отвязывается: сам файл удаляется, когда на него больше нет
        ссылок.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        media = await self._get_media_row(
            request=request,
            media_key=media_key,
            error=error,
        )

        if lesson_id is not None:
            link_result = await self.db.execute(
                select(LessonMedia).where(
                    LessonMedia.media_id == media.media_id,
                    LessonMedia.lesson_id == lesson_id,
                )
            )

            if link_result.scalar_one_or_none() is None:
                # файл не привязан к этому уроку
                await self._raise(
                    request=request,
                    code="MEDIA_FILE_NOT_FOUND",
                    error=error,
                )

            await self.db.execute(
                delete(LessonMedia).where(
                    LessonMedia.media_id == media.media_id,
                    LessonMedia.lesson_id == lesson_id,
                )
            )

            await self.db.commit()

            links_result = await self.db.execute(
                select(func.count(LessonMedia.lesson_id))
                .where(LessonMedia.media_id == media.media_id)
            )

            links = links_result.scalar_one()

            # файл ещё нужен другому уроку — сам объект не трогаем
            if links:
                logging.info(
                    "media detached from lesson: media=%s lesson=%s links=%s",
                    media.media_key,
                    lesson_id,
                    links,
                )

                return await self._empty_list()

        await self.db.delete(media)
        await self.db.commit()

        await minio_storage.delete_file(
            file_path=media.object_key,
            bucket=MEDIA_BUCKET,
        )

        logging.info("media deleted: media=%s", media.media_key)

        return await self._empty_list()

    # ---------- служебное ----------

    async def _get_media_row(
            self,
            request: Request,
            media_key: str,
            error: dict,
    ) -> MediaFile:
        """ЗАПИСЬ МЕДИАФАЙЛА"""

        result = await self.db.execute(
            select(MediaFile).where(MediaFile.media_key == media_key)
        )

        media = result.scalar_one_or_none()

        if media is None:
            await self._raise(
                request=request,
                code="MEDIA_FILE_NOT_FOUND",
                error=error,
            )

        return media

    async def _check_media_access(
            self,
            request: Request,
            media: MediaFile,
            is_admin: bool,
            user_id: int | None,
            error: dict,
    ) -> None:
        """ПРОВЕРЯЕТ ПРАВА НА МЕДИАФАЙЛ

        Ссылку на файл получает только тот, кто имеет доступ к курсу.
        """

        if is_admin:
            return

        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=media.course_id,
        )

        if not is_enrolled:
            await self._raise(
                request=request,
                code="COURSE_ACCESS_REQUIRED",
                error=error,
            )

    async def _resolve_kind(
            self,
            request: Request,
            file,
            error: dict,
    ) -> str:
        """ОПРЕДЕЛЯЕТ ТИП ФАЙЛА ПО ТИПУ И РАСШИРЕНИЮ"""

        content_type = (file.content_type or "").lower()

        file_name = (file.filename or "").lower()

        if content_type in settings.media_allowed_image_types or any(
            file_name.endswith(extension) for extension in _IMAGE_EXTENSIONS
        ):
            return MEDIA_KIND_IMAGE

        if content_type in settings.media_allowed_video_types or any(
            file_name.endswith(extension) for extension in _VIDEO_EXTENSIONS
        ):
            return MEDIA_KIND_VIDEO

        await self._raise(
            request=request,
            code="MEDIA_FILE_TYPE_NOT_ALLOWED",
            error=error,
        )

    async def _prepare_image(
            self,
            request: Request,
            file,
            error: dict,
    ):
        """ЧИТАЕТ И КОНВЕРТИРУЕТ ИЗОБРАЖЕНИЕ"""

        data = await file.read(settings.media_max_image_size + 1)

        if len(data) > settings.media_max_image_size:
            await self._raise(
                request=request,
                code="MEDIA_FILE_TOO_LARGE",
                error=error,
            )

        try:
            return await image_convertor.to_webp(
                data=data,
                content_type=file.content_type,
            )

        except ImageValidationError as error_:
            await self._raise(
                request=request,
                code=error_.code,
                error=error,
            )

    async def _prepare_video(
            self,
            request: Request,
            file,
            error: dict,
    ):
        """ПРОВЕРЯЕТ ВИДЕО И ГОТОВИТ ЕГО К ЗАГРУЗКЕ

        Файл не читается в память целиком: по структуре контейнера
        определяются кодеки и разрешение, дальше файл уходит в MinIO
        потоком.
        """

        file_object = file.file

        file_object.seek(0, 2)
        size_bytes = file_object.tell()
        file_object.seek(0)

        if size_bytes > settings.media_max_video_size:
            await self._raise(
                request=request,
                code="MEDIA_FILE_TOO_LARGE",
                error=error,
            )

        if size_bytes == 0:
            await self._raise(
                request=request,
                code="MEDIA_FILE_CORRUPTED",
                error=error,
            )

        try:
            info = video_inspector.inspect(file_object)

        except VideoValidationError as error_:
            await self._raise(
                request=request,
                code=error_.code,
                error=error,
            )

        if info.video_codec != _REQUIRED_VIDEO_CODEC:
            await self._raise(
                request=request,
                code="MEDIA_VIDEO_CODEC_NOT_SUPPORTED",
                error=error,
            )

        if info.audio_codec is not None and info.audio_codec != _REQUIRED_AUDIO_CODEC:
            await self._raise(
                request=request,
                code="MEDIA_VIDEO_CODEC_NOT_SUPPORTED",
                error=error,
            )

        if info.width and info.height:
            if info.width > settings.media_max_video_dimension or \
                    info.height > settings.media_max_video_dimension:
                await self._raise(
                    request=request,
                    code="MEDIA_VIDEO_RESOLUTION_TOO_LARGE",
                    error=error,
                )

        # файл читался с середины — возвращаем в начало для загрузки
        file_object.seek(0)

        return _PreparedVideo(
            payload=file_object,
            size_bytes=size_bytes,
            width=info.width,
            height=info.height,
            duration_seconds=info.duration_seconds,
            video_codec=info.video_codec,
            audio_codec=info.audio_codec,
        )

    @staticmethod
    def _get_original_name(file) -> str | None:
        """ИМЯ ФАЙЛА, КОТОРОЕ ЗАГРУЗИЛ ПОЛЬЗОВАТЕЛЬ"""

        name = file.filename

        if not name:
            return None

        return name[:255]

    @staticmethod
    def _to_response(
            media: MediaFile,
            lesson_id: int | None,
            url: str | None,
    ) -> MediaInfoResponse:
        """ОТВЕТ API С МЕТАДАННЫМИ МЕДИАФАЙЛА"""

        return MediaInfoResponse(
            media_id=media.media_id,
            media_key=media.media_key,
            course_id=media.course_id,
            lesson_id=lesson_id,
            kind=media.kind,
            content_type=media.content_type,
            size_bytes=media.size_bytes,
            width=media.width,
            height=media.height,
            duration_seconds=float(media.duration_seconds) if media.duration_seconds is not None else None,
            video_codec=media.video_codec,
            audio_codec=media.audio_codec,
            original_name=media.original_name,
            created_at=media.created_at,
            url=url,
        )

    async def _empty_list(self) -> MediaListResponse:
        """ПУСТОЙ СПИСОК ПОСЛЕ УДАЛЕНИЯ"""

        return MediaListResponse(
            media=[],
            total_pages=0,
            current_page=1,
            page_size=0,
        )


class _PreparedVideo:
    """ПРОВЕРЕННОЕ ВИДЕО, ГОТОВОЕ К ЗАГРУЗКЕ"""

    def __init__(
            self,
            payload,
            size_bytes: int,
            width: int | None,
            height: int | None,
            duration_seconds: float | None,
            video_codec: str | None,
            audio_codec: str | None,
    ):
        self.payload = payload
        self.size_bytes = size_bytes
        self.width = width
        self.height = height
        self.duration_seconds = duration_seconds
        self.video_codec = video_codec
        self.audio_codec = audio_codec
