"""СХЕМЫ ПРАВИЛЬНЫХ ОТВЕТОВ НА ЗАДАНИЯ"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# идентификатор задания: буквы, цифры, дефис и подчёркивание
EXERCISE_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"

# максимальная длина правильного ответа
MAX_ANSWER_LENGTH = 10000


# ЗАПРОС НА СОХРАНЕНИЕ ПРАВИЛЬНОГО ОТВЕТА
class ExerciseAnswerRequest(BaseModel):
    answer: str = Field(
        ...,
        min_length=1,
        max_length=MAX_ANSWER_LENGTH,
        examples=["print"],
    )


# ПРАВИЛЬНЫЙ ОТВЕТ НА ЗАДАНИЕ
class ExerciseAnswerResponse(BaseModel):
    answer_id: int
    lesson_id: int
    # идентификатор задания из Markdown урока
    exercise_id: str
    answer: str

    created_at: datetime
    updated_at: datetime


# СПИСОК ПРАВИЛЬНЫХ ОТВЕТОВ УРОКА
class ExerciseAnswersResponse(BaseModel):
    lesson_id: int
    answers: list[ExerciseAnswerResponse] = Field(default_factory=list)


class CodeSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exercise_id: str = Field(pattern=EXERCISE_ID_PATTERN)
    language: Literal["sql", "python"]
    code: str = Field(min_length=1, max_length=8000)

    @field_validator("code")
    @classmethod
    def nonempty_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Reference solution must not be empty")
        return value


class LessonCodeContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(max_length=1_000_000)
    version: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    solutions: list[CodeSolution] = Field(default_factory=list, max_length=500)


class LessonCodeContentResponse(LessonCodeContentRequest):
    version: str
