from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: UUID
    question: str = Field(min_length=1, max_length=2000)
    user_context: str = Field(default="", max_length=1000)


class AIMessageResponse(BaseModel):
    question_id: int
    request_id: UUID
    question: str
    user_context: str
    answer: str | None
    status: Literal["pending", "completed", "refused", "failed"]
    created_at: datetime
    error_code: str | None = None


class AIHistoryResponse(BaseModel):
    messages: list[AIMessageResponse]
    next_after_id: int | None = None
