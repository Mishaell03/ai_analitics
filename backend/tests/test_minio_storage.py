import asyncio

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

    def get_object(self, bucket_name: str, object_name: str) -> FakeResponse:
        if self._error is not None:
            raise self._error

        self.response = FakeResponse(self._data or b"")

        return self.response


class FakeStatClient:
    def __init__(self, error: Exception | None = None):
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def stat_object(self, bucket_name: str, object_name: str) -> object:
        self.calls.append((bucket_name, object_name))

        if self._error is not None:
            raise self._error

        return object()


def make_s3_error() -> S3Error:
    return S3Error(
        response=None,
        code="NoSuchKey",
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
        storage.get_text(file_path="course/1/1.md", bucket="lesson-content")
    )

    assert content == "# Урок\n"
    assert client.response is not None
    assert client.response.closed is True


def test_get_text_returns_none_for_missing_file(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeMinioClient(error=make_s3_error()))

    storage = MinioStorageService()

    content = asyncio.run(
        storage.get_text(file_path="course/1/1.md", bucket="lesson-content")
    )

    assert content is None


def test_get_text_truncates_big_file(monkeypatch):
    client = FakeMinioClient(data=b"a" * 100)

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    content = asyncio.run(
        storage.get_text(
            file_path="course/1/1.md",
            bucket="lesson-content",
            max_bytes=10,
        )
    )

    assert content == "a" * 10


def test_exists_returns_true_for_existing_file(monkeypatch):
    client = FakeStatClient()

    monkeypatch.setattr(settings, "minio_client", client)

    storage = MinioStorageService()

    exists = asyncio.run(
        storage.exists(file_path="course/1/1.md", bucket="lesson-content")
    )

    assert exists is True
    assert client.calls == [("lesson-content", "course/1/1.md")]


def test_exists_returns_false_for_missing_file(monkeypatch):
    monkeypatch.setattr(settings, "minio_client", FakeStatClient(error=make_s3_error()))

    storage = MinioStorageService()

    exists = asyncio.run(
        storage.exists(file_path="course/1/1.md", bucket="lesson-content")
    )

    assert exists is False
