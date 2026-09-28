from datetime import datetime
from sqlalchemy import (
    DateTime,
    Integer,
    String,
    func,
    Identity,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# V3__backend_errors
class BackendError(Base):
    __tablename__ = "backend_errors"
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    localizations: Mapped[list["BackendErrorLocalization"]] = relationship(
        "BackendErrorLocalization",
        back_populates="error",
        cascade="all, delete-orphan",
    )
    event_logs: Mapped[list["UserEventLog"]] = relationship(
        "UserEventLog",
        back_populates="backend_error",
        primaryjoin="BackendError.code == UserEventLog.event",
        foreign_keys="UserEventLog.event",
        viewonly=True,
    )

class BackendErrorLocalization(Base):
    __tablename__ = "backend_errors_localization"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(32), ForeignKey("backend_errors.code", ondelete="CASCADE", ),
                                      nullable=False)
    language: Mapped[str] = mapped_column(String(3), nullable=False)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped["BackendError"] = relationship("BackendError", back_populates="localizations")

    __table_args__ = (
        UniqueConstraint(
            "code",
            "language",
            name="uq_backend_errors_localization_code_language",
        ),
    )

class UserEventLog(Base):
    __tablename__ = "users_event_logs"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", ),
                                                nullable=True)
    session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users_sessions.id", ondelete="CASCADE", ),
                                                   nullable=True)
    event: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_method: Mapped[str] = mapped_column(String(16), nullable=False)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    is_proxy: Mapped[bool | None] = mapped_column(nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User | None"] = relationship("User", back_populates="event_logs")
    session: Mapped["UserSession | None"] = relationship("UserSession", back_populates="event_logs")
    backend_error: Mapped["BackendError | None"] = relationship("BackendError",
                                                                primaryjoin="foreign(UserEventLog.event) == BackendError.code",
                                                                foreign_keys=[event], viewonly=True)