"""СХЕМЫ МЕДИАФАЙЛОВ"""

from datetime import datetime

from pydantic import BaseModel, Field

# типы медиафайлов
MEDIA_KIND_IMAGE = "image"
MEDIA_KIND_VIDEO = "video"

# префикс ссылки на медиафайл в Markdown: ![описание](asset:media_key)
ASSET_REFERENCE_PREFIX = "asset:"


# МЕТАДАННЫЕ МЕДИАФАЙЛА
class MediaInfoResponse(BaseModel):
    media_id: int
    # стабильный логический идентификатор, не зависит от пути в MinIO
    media_key: str
    course_id: int
    lesson_id: int | None = None

    kind: str
    content_type: str
    size_bytes: int

    width: int | None = None
    height: int | None = None

    duration_seconds: float | None = None
    video_codec: str | None = None
    audio_codec: str | None = None

    original_name: str | None = None

    created_at: datetime

    # presigned URL выдаётся по запросу и в базе не хранится
    url: str | None = None


# СПИСОК МЕДИАФАЙЛОВ УРОКА
class MediaListResponse(BaseModel):
    media: list[MediaInfoResponse] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int


# ССЫЛКА НА ПРОСМОТР ФАЙЛА
class MediaUrlResponse(BaseModel):
    media_id: int
    media_key: str
    url: str
    content_type: str
    size_bytes: int
    # через сколько секунд ссылка перестанет работать
    expires_in: int


# ОБЛОЖКА КУРСА
class CourseImageResponse(BaseModel):
    file_id: str
    course_id: int

    content_type: str
    size_bytes: int

    width: int
    height: int

    created_at: datetime
    updated_at: datetime

    # presigned URL выдаётся по запросу и в базе не хранится
    url: str | None = None
