from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User
from app.models.auth import UserSession
from app.core.errors import raise_backend_error

security = HTTPBearer()


async def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db),
) -> User:
    session_token = credentials.credentials.strip()

    if not session_token:
        await raise_backend_error(
            db=db,
            request=request,
            code="INVALID_SESSION",
            language="en",
        )

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserSession).where(
            UserSession.session == session_token,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        await raise_backend_error(
            db=db,
            request=request,
            code="INVALID_SESSION",
            language="en",
        )

    result = await db.execute(
        select(User).where(User.user_id == session.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        await raise_backend_error(
            db=db,
            request=request,
            code="USER_NOT_FOUND",
            language=session.language,
            session_id=session.id,
            user_id=session.user_id,
        )

    if user.is_blocked:
        await raise_backend_error(
            db=db,
            request=request,
            code="USER_BLOCKED",
            language=session.language,
            session_id=session.id,
            user_id=user.user_id,
        )

    return user


async def get_current_admin(
        request: Request,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> User:
    if not user.is_admin:
        await raise_backend_error(
            db=db,
            request=request,
            code="ADMIN_ACCESS_REQUIRED",
            language="en",
            user_id=user.user_id,
        )

    return user
