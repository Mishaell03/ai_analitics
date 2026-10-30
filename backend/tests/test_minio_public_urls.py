import asyncio
from urllib.parse import parse_qs, urlsplit

import pytest
from minio import Minio

from app.core.config import settings
from app.core.minio_url import MinioStorageService


@pytest.fixture
def public_storage(monkeypatch):
    public_client = Minio(
        "s3.example.com", access_key="test-access", secret_key="test-secret",
        secure=True, region="us-east-1",
    )
    monkeypatch.setattr(settings, "_minio_public_client", public_client)
    monkeypatch.setattr(settings, "minio_public_endpoint", "s3.example.com")
    monkeypatch.setattr(settings, "minio_public_secure", True)
    monkeypatch.setattr(settings, "minio_endpoint", "minio:9000")
    monkeypatch.setattr(settings, "minio_secure", False)
    return MinioStorageService()


def test_get_url_checks_internal_storage_and_signs_public_host(public_storage, monkeypatch):
    calls = []

    class InternalClient:
        def stat_object(self, bucket_name, object_name):
            calls.append((bucket_name, object_name))

    monkeypatch.setattr(settings, "minio_client", InternalClient())
    url = asyncio.run(public_storage.get_url("1/lesson.md", "course-content"))

    assert calls == [("course-content", "1/lesson.md")]
    parsed = urlsplit(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "s3.example.com"
    assert parsed.path == "/course-content/1/lesson.md"
    assert "X-Amz-Signature" in parse_qs(parsed.query)


def test_upload_uses_public_address_without_network(public_storage):
    upload = asyncio.run(public_storage.get_upload_url(
        "course-content", "1/lesson.md", 512000, "text/markdown",
    ))

    assert upload["url"] == "https://s3.example.com/course-content"
    assert "x-amz-signature" in upload["fields"]


def test_without_public_endpoint_preserves_internal_client(monkeypatch):
    monkeypatch.setattr(settings, "_minio_public_client", None)
    monkeypatch.setattr(settings, "minio_public_endpoint", "")
    monkeypatch.setattr(settings, "minio_endpoint", "localhost:9000")
    monkeypatch.setattr(settings, "minio_secure", False)

    assert settings.minio_presign_client is settings.minio_client
    assert MinioStorageService.get_post_url("avatars") == "http://localhost:9000/avatars"
