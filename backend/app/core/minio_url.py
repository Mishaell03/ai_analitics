import asyncio
from datetime import timedelta

from fastapi import UploadFile
from minio.datatypes import PostPolicy
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

    async def get_upload_url(
        self,
        bucket: str,
        file_path: str,
        max_size: int,
        content_type: str,
        expires: int | timedelta | None = None,
    ) -> dict:
        """GENERATE PRESIGNED POST FOR DIRECT CLIENT UPLOAD"""

        if expires is None:
            expires = settings.upload_url_ttl

        if isinstance(expires, int):
            expires = timedelta(seconds=expires)

        policy = PostPolicy(
            bucket_name=bucket,
            expiration=expires,
        )

        policy.add_starts_with_condition(
            "key",
            file_path,
        )

        policy.add_content_length_range(
            1,
            max_size,
        )

        policy.add_equals_condition(
            "Content-Type",
            content_type,
        )

        return await asyncio.to_thread(
            settings.minio_client.presigned_post_policy,
            policy,
        )

minio_storage = MinioStorageService()