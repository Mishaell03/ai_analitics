import asyncio

from app.core import minio_migration


class FakeStorage:
    def __init__(self, objects: set[tuple[str, str]]):
        self.objects = objects
        self.copied: list[tuple[str, str, str]] = []

    async def exists(self, file_path: str, bucket: str) -> bool:
        return (bucket, file_path) in self.objects

    async def copy_object(
        self,
        source_bucket: str,
        source_path: str,
        target_bucket: str,
        target_path: str,
    ) -> bool:
        if (source_bucket, source_path) not in self.objects:
            return False

        self.objects.add((target_bucket, target_path))
        self.copied.append((source_bucket, source_path, target_path))

        return True


def test_copy_verified_copies_and_verifies(monkeypatch):
    storage = FakeStorage(
        {("course-media", "covers/1/c_0123456789abcdef.webp")}
    )

    monkeypatch.setattr(minio_migration, "minio_storage", storage)

    copied = asyncio.run(
        minio_migration._copy_verified(
            source_bucket="course-media",
            source_key="covers/1/c_0123456789abcdef.webp",
            target_key="1/main.webp",
            overwrite=True,
        )
    )

    assert copied is True
    assert storage.copied == [
        ("course-media", "covers/1/c_0123456789abcdef.webp", "1/main.webp")
    ]


def test_copy_verified_keeps_existing_target(monkeypatch):
    storage = FakeStorage(
        {
            ("course-content", "1/1/2.md"),
            ("lesson-content", "old-course/1/2.md"),
        }
    )

    monkeypatch.setattr(minio_migration, "minio_storage", storage)

    copied = asyncio.run(
        minio_migration._copy_verified(
            source_bucket="lesson-content",
            source_key="old-course/1/2.md",
            target_key="1/1/2.md",
            overwrite=False,
        )
    )

    assert copied is True
    assert storage.copied == []


def test_copy_verified_returns_false_without_source(monkeypatch):
    storage = FakeStorage(set())

    monkeypatch.setattr(minio_migration, "minio_storage", storage)

    copied = asyncio.run(
        minio_migration._copy_verified(
            source_bucket="module-content",
            source_key="1/content.md",
            target_key="1/1/content.md",
            overwrite=False,
        )
    )

    assert copied is False
    assert storage.copied == []
