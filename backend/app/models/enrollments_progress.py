from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, SmallInteger,
                        Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

# верх шкалы correctness (CHECK 0..3): урок с такой попыткой считается завершённым
COMPLETED_CORRECTNESS = 3
# correctness отдельного пройденного задания, пока весь урок не подтверждён
PASSED_EXERCISE_CORRECTNESS = 2
# пространство имён в JSONB LessonAttempt.answers для успешных заданий
PASSED_EXERCISES_KEY = "__passed_exercises__"
# Успешный запуск для самопроверки не означает правильный ответ.
EXPERT_REVIEW_EXERCISES_KEY = "__expert_review_exercises__"


# V5__enrollments_attempts
class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    enrollment_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", ),
                                         nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE", ),
                                           nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_course_enrollments_user_id_course_id", ),
        Index("ix_course_enrollments_course_id", "course_id"),
    )


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"

    attempt_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", ),
                                         nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.lesson_id", ondelete="CASCADE", ),
                                           nullable=False)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    answers: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    correctness: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    speed: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("correctness BETWEEN 0 AND 3", name="ck_lesson_attempts_correctness", ),
        CheckConstraint("speed BETWEEN 0 AND 2", name="ck_lesson_attempts_speed", ),
        Index("ix_lesson_attempts_user_lesson", "user_id", "lesson_id"),
    )
