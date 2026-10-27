"""СХЕМЫ ПРОВЕРКИ ОТВЕТА НА ОДНО ЗАДАНИЕ"""

from pydantic import BaseModel, Field

from app.api.v1.schemas.exercises import MAX_ANSWER_LENGTH


class ExerciseCheckRequest(BaseModel):
    """Ответ одного задания в сериализованном формате frontend."""

    answer: str = Field(..., min_length=1, max_length=MAX_ANSWER_LENGTH)
