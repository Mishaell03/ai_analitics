from datetime import timedelta

from app.core.config import settings

def get_minio_url(
    file_path: str,
    expires: int | timedelta | None = None,
    bucket: str | None = None,
) -> str:
    if expires is None:
        expires = settings.content_url_ttl

    if isinstance(expires, int):
        expires = timedelta(seconds=expires)

    return settings.minio_client.presigned_get_object(
        bucket_name=bucket or settings.minio_bucket,
        object_name=file_path,
        expires=expires,
    )