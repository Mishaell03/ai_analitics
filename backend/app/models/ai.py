"""История наставника: урок → диалог пользователя → вопросы и отдельные ответы."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    conversation_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id", ondelete="CASCADE"))
    summary: Mapped[str] = mapped_column(Text, server_default="")
    # Legacy column name retained for existing databases; only local memory metadata is stored.
    provider_state: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    active_request: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    busy_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)


class AIQuestion(Base):
    __tablename__ = "ai_questions"

    question_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.conversation_id", ondelete="CASCADE"))
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    question: Mapped[str] = mapped_column(Text)
    user_context: Mapped[str] = mapped_column(Text, server_default="")
    context_snapshot: Mapped[dict] = mapped_column(JSONB)
    prompt_hash: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(16), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("conversation_id", "request_id"),
        CheckConstraint("status IN ('pending', 'completed', 'refused', 'failed')"),
        Index("ix_ai_questions_conversation_created", "conversation_id", "created_at"),
    )


class AIAnswer(Base):
    __tablename__ = "ai_answers"

    answer_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("ai_questions.question_id", ondelete="CASCADE"), unique=True)
    answer: Mapped[str] = mapped_column(Text)
    provider_response: Mapped[dict | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    output_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint("input_tokens >= 0"), CheckConstraint("output_tokens >= 0"))
