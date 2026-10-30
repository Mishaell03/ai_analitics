from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LogFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    user: str | None = Field(default=None, max_length=255)
    user_id: int | None = Field(default=None, ge=1, le=2147483647)
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        return self


class SystemLogFilters(LogFilters):
    source: Literal["event", "backend"] | None = None
    status: Literal["success", "redirect", "client_error", "server_error"] | None = None
    status_code: int | None = Field(default=None, ge=100, le=599)
    code: str | None = Field(default=None, max_length=255)
    session_id: int | None = Field(default=None, ge=1, le=2147483647)


class AILogFilters(LogFilters):
    status: Literal["pending", "completed", "refused", "failed"] | None = None


class SystemLogItem(BaseModel):
    id: int
    source: Literal["event", "backend"]
    user_id: int | None = None
    name: str | None = None
    email: str | None = None
    session_id: int | None = None
    status_code: int | None = None
    code: str | None = None
    request_method: str
    request_path: str
    created_at: datetime


class AILogItem(BaseModel):
    question_id: int
    conversation_id: int
    user_id: int
    name: str | None = None
    email: str
    lesson_id: int
    question: str
    answer: str | None = None
    model: str
    status: str
    error_code: str | None = None
    created_at: datetime


class SystemLogsResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[SystemLogItem]


class AILogsResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[AILogItem]
