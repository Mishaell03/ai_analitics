"""СХЕМЫ ПРОВЕРКИ ОТВЕТА НА ОДНО ЗАДАНИЕ"""

from pydantic import BaseModel, Field, field_validator

from app.api.v1.schemas.exercises import MAX_ANSWER_LENGTH, validate_single_choice_answer


class ExerciseCheckRequest(BaseModel):
    """Ответ одного задания в сериализованном формате frontend."""

    answer: str = Field(..., min_length=1, max_length=MAX_ANSWER_LENGTH)
    _validate_single_choice = field_validator("answer")(validate_single_choice_answer)
