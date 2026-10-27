"""СХЕМЫ ПРАВИЛЬНЫХ ОТВЕТОВ НА ЗАДАНИЯ"""

from datetime import datetime

from pydantic import BaseModel, Field

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
