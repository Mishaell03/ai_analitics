import asyncio
from types import SimpleNamespace
import pytest

from minio.error import S3Error

from app.core.config import settings
from app.core.minio_url import MinioStorageService


class FakeResponse:
    def __init__(self, data: bytes):
        self._data = data
        self.closed = False

    def read(self, amount: int | None = None) -> bytes:
        if amount is None:
            return self._data

        return self._data[:amount]

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        pass


class FakeMinioClient:
    def __init__(self, data: bytes | None = None, error: Exception | None = None):
        self._data = data
        self._error = error
        self.response: FakeResponse | None = None
        self.removed: tuple[str, str] | None = None

    def get_object(self, bucket_name: str, object_name: str) -> FakeResponse:
        if self._error is not None:
            raise self._error

        self.response = FakeResponse(self._data or b"")

        return self.response

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        if self._error is not None:
            raise self._error

        self.removed = (bucket_name, object_name)


class FakeStatClient:
    def __init__(self, error: Exception | None = None):
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def stat_object(self, bucket_name: str, object_name: str) -> object:
        self.calls.append((bucket_name, object_name))

        if self._error is not None:
            raise self._error

        return object()


def make_s3_error(code: str = "NoSuchKey") -> S3Error:
    return S3Error(
        response=None,
        code=code,
        message="The specified key does not exist.",
        resource="object",
        request_id="request-id",
        host_id="host-id",
    )


def test_get_text_reads_file(monkeypatch):
    client = FakeMinioClient(data="# Урок\n".encode("utf-8"))

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    content = asyncio.run(
        storage.get_text(file_path="course/1/2.md", bucket="course-content")
    )

    assert content == "# Урок\n"
    assert client.response is not None
    assert client.response.closed is True


def test_get_text_returns_none_for_missing_file(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeMinioClient(error=make_s3_error()))

    storage = MinioStorageService()

    content = asyncio.run(
        storage.get_text(file_path="course/1/2.md", bucket="course-content")
    )

    assert content is None


def test_get_text_truncates_big_file(monkeypatch):
    client = FakeMinioClient(data=b"a" * 100)

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    content = asyncio.run(
        storage.get_text(
            file_path="course/1/2.md",
            bucket="course-content",
            max_bytes=10,
        )
    )

    assert content == "a" * 10


def test_strict_get_text_rejects_truncation(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeMinioClient(data=b"a" * 100))
    with pytest.raises(ValueError):
        asyncio.run(MinioStorageService().get_text("lesson.md", "course-content", max_bytes=10, strict=True))


@pytest.mark.parametrize("code", ["AccessDenied", "NoSuchBucket", "InternalError"])
def test_strict_get_text_does_not_treat_storage_failure_as_empty_lesson(monkeypatch, code):
    error = make_s3_error(code)
    monkeypatch.setattr(settings, "minio_client", FakeMinioClient(error=error))
    with pytest.raises(S3Error):
        asyncio.run(MinioStorageService().get_text("lesson.md", "course-content", strict=True))


def test_delete_file_removes_object(monkeypatch):
    client = FakeMinioClient()

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    deleted = asyncio.run(
        storage.delete_file(file_path="course/1/2.md", bucket="course-content")
    )

    assert deleted is True
    assert client.removed == ("course-content", "course/1/2.md")


def test_delete_file_survives_storage_error(monkeypatch):
    client = FakeMinioClient(error=make_s3_error())

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    deleted = asyncio.run(
        storage.delete_file(file_path="course/1/2.md", bucket="course-content")
    )

    assert deleted is False


def test_exists_returns_true_for_existing_file(monkeypatch):
    client = FakeStatClient()

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    exists = asyncio.run(
        storage.exists(file_path="course/1/2.md", bucket="course-content")
    )

    assert exists is True
    assert client.calls == [("course-content", "course/1/2.md")]


def test_exists_returns_false_for_missing_file(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeStatClient(error=make_s3_error()))

    storage = MinioStorageService()

    exists = asyncio.run(
        storage.exists(file_path="course/1/2.md", bucket="course-content")
    )

    assert exists is False


class FakeCopyClient:
    def __init__(self, error: Exception | None = None):
        self._error = error
        self.copied: tuple[str, str, str, str] | None = None

    def copy_object(self, bucket_name, object_name, source) -> object:
        if self._error is not None:
            raise self._error

        self.copied = (
            source.bucket_name,
            source.object_name,
            bucket_name,
            object_name,
        )

        return object()


class FakeListClient:
    def __init__(self, keys: list[str]):
        self.keys = keys
        self.removed: list[tuple[str, str]] = []

    def list_objects(self, bucket_name, prefix=None, recursive=False):
        return [
            SimpleNamespace(object_name=key)
            for key in self.keys
            if key.startswith(prefix or "")
        ]

    def remove_object(self, bucket_name, object_name) -> None:
        self.removed.append((bucket_name, object_name))


def test_copy_object_copies_between_buckets(monkeypatch):
    client = FakeCopyClient()

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    copied = asyncio.run(
        storage.copy_object(
            source_bucket="course-media",
            source_path="covers/1/c_0123456789abcdef.webp",
            target_bucket="course-content",
            target_path="1/main.webp",
        )
    )

    assert copied is True
    assert client.copied == (
        "course-media",
        "covers/1/c_0123456789abcdef.webp",
        "course-content",
        "1/main.webp",
    )


def test_copy_object_survives_storage_error(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeCopyClient(error=make_s3_error()))

    storage = MinioStorageService()

    copied = asyncio.run(
        storage.copy_object(
            source_bucket="course-media",
            source_path="media/1/m_0123456789abcdef.webp",
            target_bucket="course-content",
            target_path="1/media/m_0123456789abcdef.webp",
        )
    )

    assert copied is False


def test_list_keys_returns_objects_under_prefix(monkeypatch):
    client = FakeListClient(
        ["1/main.webp", "1/1/2.md", "2/main.webp"]
    )

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    keys = asyncio.run(storage.list_keys(bucket="course-content", prefix="1/"))

    assert keys == ["1/main.webp", "1/1/2.md"]


def test_delete_prefix_removes_every_object(monkeypatch):
    client = FakeListClient(["1/main.webp", "1/1/2.md", "2/main.webp"])

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    deleted = asyncio.run(
        storage.delete_prefix(bucket="course-content", prefix="1/")
    )

    assert deleted == 2
    assert client.removed == [
        ("course-content", "1/main.webp"),
        ("course-content", "1/1/2.md"),
    ]
