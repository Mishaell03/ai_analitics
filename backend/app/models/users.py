from datetime import datetime
from sqlalchemy import (Boolean, DateTime, ForeignKey, Identity, Integer,
                        String, Text, UniqueConstraint, func, BigInteger)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.errors import UserEventLog


# V1__users
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, Identity(start=1_000_000), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, unique=True, nullable=False)
    img: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_default_img: Mapped[bool] = mapped_column(Boolean, default=True, server_default="false", nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    event_logs: Mapped[list["UserEventLog"]] = relationship("UserEventLog", back_populates="user")
    consents: Mapped[list["UserConsent"]] = relationship(
        "UserConsent",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# V6__user_consents
class UserConsent(Base):
    __tablename__ = "users_consents"

    consent_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    consent_code: Mapped[str] = mapped_column(String(64), nullable=False)
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), server_default="1.0", nullable=False)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="consents")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "consent_code",
            name="uq_users_consents_user_id_consent_code",
        ),
    )