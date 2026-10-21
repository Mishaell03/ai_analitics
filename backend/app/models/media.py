"""МОДЕЛИ МЕДИАФАЙЛОВ

Файлы лежат в приватном MinIO, в базе хранится только логический
идентификатор, физический ключ объекта и метаданные файла.
presigned URL не сохраняется: он выдаётся по запросу.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.courses import Course


# V7__media
class CourseImage(Base):
    """ОБЛОЖКА КУРСА"""

    __tablename__ = "course_images"

    image_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE", ),
                                           nullable=False)

    # логический идентификатор файла
    file_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # физический ключ объекта в MinIO
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    course: Mapped["Course"] = relationship("Course")


class MediaFile(Base):
    """МЕДИАФАЙЛ КУРСА (ИЗОБРАЖЕНИЕ ИЛИ ВИДЕО)"""

    __tablename__ = "media_files"

    media_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    # стабильный логический идентификатор: ![описание](asset:media_key)
    media_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE", ),
                                           nullable=False)

    # физический ключ объекта в MinIO
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)

    # image | video
    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    duration_seconds: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)

    video_codec: Mapped[str | None] = mapped_column(String(32), nullable=True)
    audio_codec: Mapped[str | None] = mapped_column(String(32), nullable=True)

    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    course: Mapped["Course"] = relationship("Course")
    lessons: Mapped[list["LessonMedia"]] = relationship("LessonMedia", back_populates="media",
                                                        cascade="all, delete-orphan")


class LessonMedia(Base):
    """СВЯЗЬ УРОКА И МЕДИАФАЙЛА

    Файл может использоваться в нескольких уроках, поэтому при удалении
    медиа сначала проверяется, что на него больше нет ссылок.
    """

    __tablename__ = "lesson_media"

    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.lesson_id", ondelete="CASCADE", ),
                                           primary_key=True)
    media_id: Mapped[int] = mapped_column(Integer, ForeignKey("media_files.media_id", ondelete="CASCADE", ),
                                          primary_key=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    media: Mapped["MediaFile"] = relationship("MediaFile", back_populates="lessons")
