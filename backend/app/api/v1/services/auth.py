import secrets
from datetime import datetime, timezone, timedelta
import random

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.v1.dto.auth_service import BaseAuthContext
from app.api.v1.schemas.auth import BaseAuthRequest, ConsentItem, RegisterRequest, _AuthData
from app.core.errors import raise_backend_error
from app.models.auth import UserAuthMethod, UserSession, Provider
from app.models.users import User, UserConsent
from app.core.clients_ip import get_client_ip
from app.utils.phone import normalize_phone

# согласия, без которых регистрация невозможна
REQUIRED_CONSENTS = frozenset({"PERSONAL_DATA"})

# версия документов, с которыми соглашается пользователь при регистрации
POLICY_VERSION = "1.0"


class BaseAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
            self,
            data: RegisterRequest,
            request: Request,
    ) -> BaseAuthContext:
        """Registration with ФИО, phone, consents and mail + password"""
        ph = PasswordHasher()

        error_kwargs = {
            "db": self.db,
            "request": request,
            "language": data.language,
            "device_id": data.device_id,
        }

        existing_user = await self._get_user_by_email(email=data.email)

        if existing_user is not None:
            await raise_backend_error(
                code="EMAIL_ALREADY_EXISTS",
                **error_kwargs,
            )

        provider = await self._get_pass_provider(error_kwargs=error_kwargs)

        consents = await self._prepare_consents(
            consents=data.consents,
            error_kwargs=error_kwargs,
        )

        phone = await self._prepare_phone(
            phone=data.phone,
            error_kwargs=error_kwargs,
        )

        random_number = random.randint(1, 11)

        # create user + get it`s id
        user = User(
            email=data.email,
            name=data.name,
            phone=phone,
            img=f'user{random_number}',
        )

        self.db.add(user)
        await self.db.flush()

        # create user login method
        auth_method = UserAuthMethod(
            user_id=user.user_id,
            provider=provider.code,
            provider_user_id=None,
            password_hash=ph.hash(data.password),
        )

        self.db.add(auth_method)

        # remember consents on data processing with ip and policy version
        client_ip = get_client_ip(request)

        for consent_code, is_accepted in consents:
            self.db.add(
                UserConsent(
                    user_id=user.user_id,
                    consent_code=consent_code,
                    is_accepted=is_accepted,
                    policy_version=POLICY_VERSION,
                    ip=client_ip,
                )
            )

        return await self._create_session(
            user=user,
            provider=provider,
            data=data,
            request=request,
            error_code="REGISTRATION_FAILED",
            error_kwargs=error_kwargs,
        )

    async def auth(
            self,
            data: BaseAuthRequest,
            request: Request,
    ) -> BaseAuthContext:
        """Authorization with mail + password"""
        ph = PasswordHasher()

        error_kwargs = {
            "db": self.db,
            "request": request,
            "language": data.language,
            "device_id": data.device_id,
        }

        user = await self._get_user_by_email(email=data.email)

        if user is None:
            await raise_backend_error(
                code="USER_NOT_FOUND",
                **error_kwargs,
            )

        provider = await self._get_pass_provider(error_kwargs=error_kwargs)

        result_auth_method = await self.db.execute(
            select(UserAuthMethod).where(
                UserAuthMethod.user_id == user.user_id,
                UserAuthMethod.provider == provider.code,
            )
        )

        auth_method = result_auth_method.scalar_one_or_none()

        if auth_method is None:
            await raise_backend_error(
                code="INCORRECT_AUTH_METHOD",
                **error_kwargs,
            )

        try:
            ph.verify(auth_method.password_hash, data.password)

        except Exception:
            await raise_backend_error(
                code="LOGIN_FAILED",
                **error_kwargs,
            )

        return await self._create_session(
            user=user,
            provider=provider,
            data=data,
            request=request,
            error_code="LOGIN_FAILED",
            error_kwargs=error_kwargs,
            revoke_device_sessions=True,
        )

    async def _get_user_by_email(self, *, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def _get_pass_provider(self, *, error_kwargs: dict) -> Provider:
        result = await self.db.execute(
            select(Provider).where(
                Provider.code == "pass"
            )
        )

        provider = result.scalar_one_or_none()

        if provider is None:
            await raise_backend_error(
                code="AUTH_PROVIDER_NOT_FOUND",
                **error_kwargs,
            )

        return provider

    async def _prepare_phone(self, *, phone: str, error_kwargs: dict) -> str:
        """Приводит телефон к каноническому виду и проверяет, что он свободен."""
        try:
            normalized = normalize_phone(phone)

        except ValueError:
            normalized = None

        if normalized is None:
            await raise_backend_error(
                code="INVALID_PHONE_FORMAT",
                **error_kwargs,
            )

        result = await self.db.execute(
            select(User.user_id)
            .where(User.phone == normalized)
            .limit(1)
        )

        if result.scalar_one_or_none() is not None:
            await raise_backend_error(
                code="PHONE_ALREADY_EXISTS",
                **error_kwargs,
            )

        return normalized

    async def _prepare_consents(
            self,
            *,
            consents: list[ConsentItem],
            error_kwargs: dict,
    ) -> list[tuple[str, bool]]:
        """Проверяет, что все обязательные согласия приняты.

        Повторяющиеся коды схлопываются, чтобы не упереться в UNIQUE(user_id, consent_code).
        """
        accepted = {
            consent.code.value: consent.is_accepted
            for consent in consents
        }

        for consent_code in REQUIRED_CONSENTS:
            if not accepted.get(consent_code, False):
                await raise_backend_error(
                    code="CONSENT_REQUIRED",
                    **error_kwargs,
                )

        return list(accepted.items())

    async def _create_session(
            self,
            *,
            user: User,
            provider: Provider,
            data: _AuthData,
            request: Request,
            error_code: str,
            error_kwargs: dict,
            revoke_device_sessions: bool = False,
    ) -> BaseAuthContext:
        now = datetime.now(timezone.utc)

        if revoke_device_sessions:
            result_device_sessions = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user.user_id,
                    UserSession.device_id == data.device_id,
                    UserSession.expires_at >= now,
                    UserSession.revoked_at.is_(None),
                )
            )

            for session in result_device_sessions.scalars().all():
                session.revoked_at = now

        session_token = secrets.token_urlsafe(64)

        user_session = UserSession(
            device_id=data.device_id,
            platform='web',
            user_id=user.user_id,
            session=session_token,
            ip=get_client_ip(request),
            language=data.language,
            provider=provider.code,
            device_name=data.device_name,
            expires_at=now + timedelta(days=180),
        )

        self.db.add(user_session)

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()

            await raise_backend_error(
                code=error_code,
                **error_kwargs,
            )

        return BaseAuthContext(
            device_id=data.device_id,
            session_id=user_session.id,
            user_id=user.user_id,
            session=session_token,
        )