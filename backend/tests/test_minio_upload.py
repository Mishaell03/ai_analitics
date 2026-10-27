import asyncio
import base64
import json

from app.core.minio_url import MinioStorageService


def get_policy_conditions(upload: dict) -> list:
    """РАЗБИРАЕТ УСЛОВИЯ ПОЛИТИКИ ЗАГРУЗКИ"""

    policy = json.loads(base64.b64decode(upload["fields"]["policy"]))

    return policy["conditions"]


def test_get_upload_url_returns_post_address_and_fields():
    storage = MinioStorageService()

    upload = asyncio.run(
        storage.get_upload_url(
            bucket="course-content",
            file_path="1/1/1.md",
            max_size=512000,
            content_type="text/markdown",
        )
    )

    assert upload["url"].endswith("/course-content")
    assert upload["fields"]["key"] == "1/1/1.md"
    assert upload["fields"]["Content-Type"] == "text/markdown"
    assert "x-amz-signature" in upload["fields"]
    assert "policy" in upload["fields"]


def test_get_upload_url_limits_file_size():
    storage = MinioStorageService()

    upload = asyncio.run(
        storage.get_upload_url(
            bucket="course-content",
            file_path="1/1/1.md",
            max_size=512000,
            content_type="text/markdown",
        )
    )

    conditions = get_policy_conditions(upload)

    # размер файла проверяет сам MinIO
    assert ["content-length-range", 1, 512000] in conditions


def test_get_upload_url_fixes_object_key():
    storage = MinioStorageService()

    upload = asyncio.run(
        storage.get_upload_url(
            bucket="course-content",
            file_path="1/1/1.md",
            max_size=512000,
            content_type="text/markdown",
        )
    )

    conditions = get_policy_conditions(upload)

    assert ["eq", "$key", "1/1/1.md"] in conditions
    assert ["eq", "$Content-Type", "text/markdown"] in conditions
