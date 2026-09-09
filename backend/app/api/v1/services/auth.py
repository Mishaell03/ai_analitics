import secrets
from datetime import datetime, timezone, timedelta

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.v1.schemas.auth import BaseRegisterRequest
from app.core.errors import raise_backend_error
from app.models.auth import UserAuthMethod, UserSession, Provider
from app.models.users import User
from app.core.clients_ip import get_client_ip


class BaseAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
            self,
            data: BaseRegisterRequest,
            request: Request,
    ) -> str:

        # test user has registration or not
        user_result = await self.db.execute(
            select(User)
            .where(User.email == data.email)
        )

        existing_user = user_result.scalar_one_or_none()

        if existing_user is not None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="EMAIL_ALREADY_EXISTS",
                language=data.language,
                device_id=data.device_id,
            )

        result_provider = await self.db.execute(
            select(Provider).where(
                Provider.code == "pass"
            )
        )

        provider = result_provider.scalar_one_or_none()

        if provider is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="AUTH_PROVIDER_NOT_FOUND",
                language=data.language,
                device_id=data.device_id,
            )

        ph = PasswordHasher()
        password_hash = ph.hash(data.password)

        # create user + get it`s id
        user = User(
            email=data.email,
        )

        self.db.add(user)
        await self.db.flush()

        # create user login method
        auth_method = UserAuthMethod(
            user_id=user.user_id,
            provider=provider.code,
            provider_user_id=None,
            password_hash=password_hash,
        )

        self.db.add(auth_method)

        client_ip = get_client_ip(request)
        session_token = secrets.token_urlsafe(64)
        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(days=180)

        user_session = UserSession(
            device_id=data.device_id,
            user_id=user.user_id,
            session=session_token,
            ip=client_ip,
            language=data.language,
            provider=provider.code,
            device_name=data.device_name,
            expires_at=expires_at,
        )

        self.db.add(user_session)

        try:
            await self.db.commit()

        except InterruptedError:
            await self.db.rollback()

            await raise_backend_error(
                db=self.db,
                request=request,
                code="REGISTRATION_FAILED",
                language=data.language,
                device_id=data.device_id,
            )

        return session_token
