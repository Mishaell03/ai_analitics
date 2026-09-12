from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.errors import UserEventLog


# V4__providers
class Provider(Base):
    __tablename__ = "providers"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


# V5__user_auth_methods
class UserAuthMethod(Base):
    __tablename__ = "user_auth_methods"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", ), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), ForeignKey("providers.code", ondelete="RESTRICT", ),
                                          nullable=False)
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_user_auth_methods_provider_provider_user_id",
        ),
    )


# V6__users_sessions
class UserSession(Base):
    __tablename__ = "users_sessions"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", ), nullable=False)
    session: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    language: Mapped[str] = mapped_column(String(3), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), ForeignKey("providers.code", ondelete="RESTRICT", ),
                                          nullable=False)
    platform: Mapped[str | None] = mapped_column(String(15), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event_logs: Mapped[list["UserEventLog"]] = relationship("UserEventLog", back_populates="session")
