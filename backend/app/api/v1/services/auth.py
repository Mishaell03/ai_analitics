import secrets
from datetime import datetime, timezone, timedelta
import random

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.v1.dto.auth_service import BaseAuthContext
from app.api.v1.schemas.auth import BaseAuthRequest
from app.core.errors import raise_backend_error
from app.models.auth import UserAuthMethod, UserSession, Provider
from app.models.users import User
from app.core.clients_ip import get_client_ip

class BaseAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
            self,
            data: BaseAuthRequest,
            request: Request,
            is_register: bool,
    ) -> BaseAuthContext:
        """Authorization with mail + password"""
        ph = PasswordHasher()

        # test user has registration or not
        user_result = await self.db.execute(
            select(User)
            .where(User.email == data.email)
        )

        existing_user = user_result.scalar_one_or_none()

        if is_register:

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

            password_hash = ph.hash(data.password)
            random_number = random.randint(1, 11)
            # create user + get it`s id
            user = User(
                email=data.email,
                img=f'user{random_number}',
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

            now = datetime.now(timezone.utc)
            error_fail = "BASE_AUTH_FAILED"

        else:
            user = existing_user

            if user is None:
                await raise_backend_error(
                    db=self.db,
                    request=request,
                    code="USER_NOT_FOUND",
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

            result_auth_method = await self.db.execute(
                select(UserAuthMethod).where(
                    UserAuthMethod.user_id == user.user_id,
                    UserAuthMethod.provider == provider.code,
                )
            )

            auth_method = result_auth_method.scalar_one_or_none()

            if auth_method is None:
                await raise_backend_error(
                    db=self.db,
                    request=request,
                    code="INCORRECT_AUTH_METHOD",
                    language=data.language,
                    device_id=data.device_id,
                )

            try:
                ph.verify(auth_method.password_hash, data.password)
            except Exception:
                await raise_backend_error(
                    db=self.db,
                    request=request,
                    code="REGISTRATION_FAILED",
                    language=data.language,
                    device_id=data.device_id,
                )

            now = datetime.now(timezone.utc)

            result_device_id = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user.user_id,
                    UserSession.device_id == data.device_id,
                    UserSession.expires_at >= now,
                    UserSession.revoked_at.is_(None),
                )
            )

            device_id = result_device_id.scalars().all()

            for session in device_id:
                session.revoked_at = now

            error_fail = "BASE_LOGIN_FAILED"

        client_ip = get_client_ip(request)
        session_token = secrets.token_urlsafe(64)

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

        except IntegrityError:
            await self.db.rollback()

            await raise_backend_error(
                db=self.db,
                request=request,
                code=error_fail,
                language=data.language,
                device_id=data.device_id,
            )

        return BaseAuthContext(
            device_id=data.device_id,
            session_id=user_session.id,
            user_id=user.user_id,
            session=session_token,
        )
