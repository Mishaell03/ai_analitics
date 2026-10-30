import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import UploadFile
from minio.commonconfig import CopySource
from minio.datatypes import Object, PostPolicy
from minio.error import S3Error

from app.core.config import settings


class MinioStorageService:

    async def get_url(
        self,
        file_path: str,
        bucket: str,
        expires: int | timedelta | None = None,
        check_exists: bool = True,
    ) -> str | None:
        """GET URL FOR FILE"""

        if expires is None:
            expires = settings.content_url_ttl

        if isinstance(expires, int):
            expires = timedelta(seconds=expires)

        if check_exists:
            try:
                await asyncio.to_thread(
                    settings.minio_client.stat_object,
                    bucket_name=bucket,
                    object_name=file_path,
                )
            except S3Error as exc:
                if exc.code in ("NoSuchKey", "NoSuchBucket"):
                    return None
                logging.warning(f"MinIO S3 error checking {bucket}/{file_path}: {exc}")
                return None
            except Exception as exc:
                logging.warning(f"MinIO connection/network error checking {bucket}/{file_path}: {exc}")
                return None

        try:
            return await asyncio.to_thread(
                settings.minio_presign_client.presigned_get_object,
                bucket_name=bucket,
                object_name=file_path,
                expires=expires,
            )
        except Exception as exc:
            logging.error(f"Failed to generate presigned GET URL for {bucket}/{file_path}: {exc}")
            return None

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
        except Exception as exc:
            logging.warning(f"MinIO connection error checking exists for {bucket}/{file_path}: {exc}")
            return False

        return True

    async def ensure_bucket(self, bucket: str) -> bool:
        """СОЗДАЁТ БАК, ЕСЛИ ЕГО ЕЩЁ НЕТ"""

        def _ensure() -> bool:
            if settings.minio_client.bucket_exists(bucket):
                return True

            settings.minio_client.make_bucket(bucket)

            return True

        try:
            return await asyncio.to_thread(_ensure)

        except S3Error:
            logging.warning(f"failed to ensure bucket: {bucket}")

            return False

    async def copy_object(
        self,
        source_bucket: str,
        source_path: str,
        target_bucket: str,
        target_path: str,
    ) -> bool:
        """КОПИРУЕТ ОБЪЕКТ ВНУТРИ ХРАНИЛИЩА

        Используется миграцией: исходный объект остаётся на месте,
        пока получатель не проверит, что копия действительно появилась.
        """

        if source_bucket == target_bucket and source_path == target_path:
            return True

        try:
            await asyncio.to_thread(
                settings.minio_client.copy_object,
                bucket_name=target_bucket,
                object_name=target_path,
                source=CopySource(source_bucket, source_path),
            )

        except S3Error:
            logging.warning(
                f"failed to copy object: "
                f"{source_bucket}/{source_path} -> {target_bucket}/{target_path}"
            )

            return False

        return True

    async def list_keys(
        self,
        bucket: str,
        prefix: str = "",
    ) -> list[str]:
        """СПИСОК КЛЮЧЕЙ ОБЪЕКТОВ В БАКЕ"""

        def _list() -> list[str]:
            return [
                item.object_name
                for item in settings.minio_client.list_objects(
                    bucket_name=bucket,
                    prefix=prefix,
                    recursive=True,
                )
            ]

        try:
            return await asyncio.to_thread(_list)

        except S3Error:
            logging.warning(f"failed to list objects: {bucket}/{prefix}")

            return []

    async def delete_prefix(
        self,
        bucket: str,
        prefix: str,
    ) -> int:
        """УДАЛЯЕТ ВСЕ ОБЪЕКТЫ ПОД ПРЕФИКСОМ

        Возвращает количество удалённых объектов.
        """

        keys = await self.list_keys(bucket=bucket, prefix=prefix)

        deleted = 0

        for key in keys:
            if await self.delete_file(file_path=key, bucket=bucket):
                deleted += 1

        return deleted

    async def get_text(
        self,
        file_path: str,
        bucket: str,
        max_bytes: int | None = None,
        strict: bool = False,
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

            except S3Error as exc:
                if strict and exc.code != "NoSuchKey":
                    raise
                return None

            finally:
                if response is not None:
                    response.close()
                    response.release_conn()

            if len(data) > limit:
                if strict:
                    raise ValueError("Text file exceeds size limit")
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
            settings.minio_presign_client.presigned_post_policy,
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

        endpoint = settings.minio_public_endpoint or settings.minio_endpoint
        secure = (
            settings.minio_public_secure
            if settings.minio_public_endpoint else settings.minio_secure
        )
        scheme = "https" if secure else "http"

        return f"{scheme}://{endpoint}/{bucket}"

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
