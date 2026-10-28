"""ПРАВИЛЬНЫЕ ОТВЕТЫ НА ЗАДАНИЯ УРОКОВ

Задания (тесты) лежат в Markdown урока, правильные ответы — здесь.
Связь идёт через exercise_id: он указан в Markdown и повторяется
в ключе записи, поэтому ответ переживает правку текста задания.
"""

from datetime import datetime

from sqlalchemy import (
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
from app.models.courses import Lesson


# V8__exercise_answers
class ExerciseAnswer(Base):
    """ПРАВИЛЬНЫЙ ОТВЕТ НА ЗАДАНИЕ УРОКА"""

    __tablename__ = "exercise_answers"

    answer_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.lesson_id", ondelete="CASCADE", ),
                                           nullable=False)

    # идентификатор задания из Markdown урока
    exercise_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # Кодовые блоки: JSON {type: code, language, value, execution}.
    # Эталон и результат его выполнения доступны только админскому API.
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    lesson: Mapped["Lesson"] = relationship("Lesson")

    __table_args__ = (
        UniqueConstraint("lesson_id", "exercise_id", name="uq_exercise_answers_lesson_id_exercise_id", ),
    )
