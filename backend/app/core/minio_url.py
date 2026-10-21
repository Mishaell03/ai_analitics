import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import UploadFile
from minio.datatypes import Object, PostPolicy
from minio.error import S3Error

from app.core.config import settings


class MinioStorageService:

    async def get_url(
        self,
        file_path: str,
        bucket: str,
        expires: int | timedelta | None = None,
    ) -> str | None:
        """GET URL FOR FILE"""

        if expires is None:
            expires = settings.content_url_ttl

        if isinstance(expires, int):
            expires = timedelta(seconds=expires)

        try:
            await asyncio.to_thread(
                settings.minio_client.stat_object,
                bucket_name=bucket,
                object_name=file_path,
            )
        except S3Error:
            return None

        return await asyncio.to_thread(
            settings.minio_client.presigned_get_object,
            bucket_name=bucket,
            object_name=file_path,
            expires=expires,
        )

    async def exists(
        self,
        file_path: str,
        bucket: str,
    ) -> bool:
        """ЕСТЬ ЛИ ФАЙЛ В БАКЕ

        Отдельный метод, а не get_url: ссылка нужна не всегда,
        достаточно знать, что объект существует.
        """

        try:
            await asyncio.to_thread(
                settings.minio_client.stat_object,
                bucket_name=bucket,
                object_name=file_path,
            )
        except S3Error:
            return False

        return True

    async def get_text(
        self,
        file_path: str,
        bucket: str,
        max_bytes: int | None = None,
    ) -> str | None:
        """READ TEXT FILE FROM BUCKET

        None, если объекта нет в баке. Файл читается с ограничением
        по размеру, чтобы один большой объект не съел память процесса.
        """

        limit = max_bytes if max_bytes is not None else settings.max_text_file_size

        def _read() -> str | None:
            response = None

            try:
                response = settings.minio_client.get_object(
                    bucket_name=bucket,
                    object_name=file_path,
                )

                # читаем на один байт больше лимита, чтобы понять,
                # что файл не помещается в ограничение
                data = response.read(limit + 1)

            except S3Error:
                return None

            finally:
                if response is not None:
                    response.close()
                    response.release_conn()

            if len(data) > limit:
                logging.warning(
                    f"file is too large and was truncated: {bucket}/{file_path}"
                )

                data = data[:limit]

            return data.decode("utf-8-sig", errors="replace")

        return await asyncio.to_thread(_read)

    async def upload_file(
        self,
        file: UploadFile,
        bucket: str,
        file_path: str,
    ) -> None:
        """UPLOAD FILE FROM BACKEND"""

        content_type = (
            file.content_type
            or "application/octet-stream"
        )

        file_object = file.file

        file_object.seek(0, 2)
        file_size = file_object.tell()
        file_object.seek(0)

        await asyncio.to_thread(
            settings.minio_client.put_object,
            bucket_name=bucket,
            object_name=file_path,
            data=file_object,
            length=file_size,
            content_type=content_type,
        )

    async def put_stream(
        self,
        data,
        length: int,
        bucket: str,
        file_path: str,
        content_type: str,
    ) -> None:
        """ЗАГРУЖАЕТ ПОТОК В БАКЕТ

        Данные не читаются в память целиком: MinIO тянет их из
        переданного потока частями, поэтому так можно грузить видео.
        """

        await asyncio.to_thread(
            settings.minio_client.put_object,
            bucket_name=bucket,
            object_name=file_path,
            data=data,
            length=length,
            content_type=content_type,
        )

    async def stat(
        self,
        file_path: str,
        bucket: str,
    ) -> Object | None:
        """МЕТАДАННЫЕ ОБЪЕКТА В БАКЕТЕ

        None, если объекта нет.
        """

        try:
            return await asyncio.to_thread(
                settings.minio_client.stat_object,
                bucket_name=bucket,
                object_name=file_path,
            )

        except S3Error:
            return None

    async def get_upload_url(
        self,
        bucket: str,
        file_path: str,
        max_size: int,
        content_type: str,
        expires: int | timedelta | None = None,
    ) -> dict:
        """GENERATE PRESIGNED POST FOR DIRECT CLIENT UPLOAD

        Возвращает:
            url    — адрес, куда клиент отправляет файл;
            fields — поля формы, которые нужно отправить вместе с файлом.

        Ограничение по размеру проверяет сам MinIO: если файл больше
        max_size, загрузка отклоняется с ошибкой на стороне MinIO.
        """

        if expires is None:
            expires = settings.upload_url_ttl

        if isinstance(expires, int):
            expires = timedelta(seconds=expires)

        # политика живёт до конкретного момента, а не на интервал
        expiration = datetime.now(timezone.utc) + expires

        policy = PostPolicy(
            bucket_name=bucket,
            expiration=expiration,
        )

        # ключ объекта фиксирован: клиент пишет ровно в этот файл
        policy.add_equals_condition(
            "key",
            file_path,
        )

        policy.add_content_length_range_condition(
            1,
            max_size,
        )

        policy.add_equals_condition(
            "Content-Type",
            content_type,
        )

        form_data = await asyncio.to_thread(
            settings.minio_client.presigned_post_policy,
            policy,
        )

        return {
            "url": self.get_post_url(bucket),
            "fields": {
                **form_data,
                "key": file_path,
                "Content-Type": content_type,
            },
        }

    @staticmethod
    def get_post_url(bucket: str) -> str:
        """АДРЕС БАКЕТА ДЛЯ ПРЯМОЙ ЗАГРУЗКИ ФАЙЛА (POST)"""

        scheme = "https" if settings.minio_secure else "http"

        return f"{scheme}://{settings.minio_endpoint}/{bucket}"

    async def delete_file(
        self,
        file_path: str,
        bucket: str,
    ) -> bool:
        """УДАЛЯЕТ ФАЙЛ ИЗ БАКЕТА

        True, если файл удалён или его не было. Ошибка хранилища
        не ломает операцию: файл можно удалить и позже.
        """

        try:
            await asyncio.to_thread(
                settings.minio_client.remove_object,
                bucket_name=bucket,
                object_name=file_path,
            )

        except S3Error:
            logging.warning(f"failed to delete file: {bucket}/{file_path}")

            return False

        return True

minio_storage = MinioStorageService()