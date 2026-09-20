from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import raise_backend_error
from app.models.auth import UserSession
from app.models.users import User


class CurrentUserContext:
    def __init__(
        self,
        user: User,
        session: UserSession,
    ):
        self.user = user
        self.session = session

async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
) -> CurrentUserContext:

    session_token = request.cookies.get("session_token")

    if not session_token:
        await raise_backend_error(
            db=db,
            request=request,
            code="INVALID_SESSION",
            language="en",
        )

    session_token = session_token.strip()

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
        select(User).where(
            User.user_id == session.user_id,
        )
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

    return CurrentUserContext(
        user=user,
        session=session,
    )


async def get_current_admin(
        request: Request,
        current: CurrentUserContext = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> CurrentUserContext:

    if not current.user.is_admin:
        await raise_backend_error(
            db=db,
            request=request,
            code="ADMIN_ACCESS_REQUIRED",
            language=current.session.language,
            session_id=current.session.id,
            user_id=current.user.user_id,
        )

    return current
