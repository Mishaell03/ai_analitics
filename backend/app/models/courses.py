from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# V4__courses
class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)
    modules: Mapped[list["CourseModule"]] = relationship("CourseModule", back_populates="course",
                                                         cascade="all, delete-orphan")

class CourseModule(Base):
    __tablename__ = "course_modules"

    module_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE", ),
                                           nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)
    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("course_id", "position", name="uq_course_modules_course_id_position", ), )

class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_modules.module_id", ondelete="CASCADE", ),
                                           nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)
    module: Mapped["CourseModule"] = relationship("CourseModule", back_populates="lessons")

    __table_args__ = (UniqueConstraint("module_id", "position", name="uq_lessons_module_id_position", ), )
