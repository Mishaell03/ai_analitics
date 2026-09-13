from datetime import timedelta
from minio.error import S3Error

from app.core.config import settings

async def get_minio_url(
    file_path: str,
    expires: int | timedelta | None = None,
    bucket: str | None = None,
) -> str | None:
    if expires is None:
        expires = settings.content_url_ttl

    if isinstance(expires, int):
        expires = timedelta(seconds=expires)

    try:
        settings.minio_client.stat_object(
            bucket_name=bucket,
            object_name=file_path,
        )
    except S3Error:
        return None

    return settings.minio_client.presigned_get_object(
        bucket_name=bucket or settings.minio_bucket,
        object_name=file_path,
        expires=expires,
    )