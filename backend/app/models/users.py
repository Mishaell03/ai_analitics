from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, Identity
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
