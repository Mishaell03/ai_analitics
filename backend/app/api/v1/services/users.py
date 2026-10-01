from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from starlette.requests import Request

from app.api.v1.schemas.users import MeResponse, MeUpdateRequest
from app.core.config import settings
from app.core.errors import raise_backend_error
from app.core.minio_url import minio_storage
from app.core.session import CurrentUserContext
from app.models.users import User
from app.utils.phone import normalize_phone


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_me(
        self,
        current_user: CurrentUserContext,
    ) -> MeResponse:
        user = current_user.user
        session = current_user.session

        img_url = None

        if user.img:
            img_url = await minio_storage.get_url(
                file_path=user.img + ".webp",
                bucket="avatars" if not user.is_default_img else "default-avatars",
                expires=settings.image_url_ttl,
            )

        return MeResponse(
            name=user.name,
            phone=user.phone,
            email=user.email,
            img_url=img_url,
            is_admin=user.is_admin,
            expires_at=session.expires_at
        )

    async def update_me(
        self,
        current_user: CurrentUserContext,
        data: MeUpdateRequest,
        request: Request,
    ) -> MeResponse:
        user = current_user.user
        user_session = current_user.session

        error_kwargs = {
            "db": self.db,
            "request": request,
            "language": user_session.language,
            "device_id": user_session.device_id,
            "session_id": user_session.id,
            "user_id": user.user_id,
            "platform": user_session.platform,
        }

        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("email") is None:
            update_data.pop("email", None)

        phone_is_set = "phone" in update_data
        phone = update_data.pop("phone", None)

        if phone_is_set:
            try:
                phone = normalize_phone(phone)

            except ValueError:
                await raise_backend_error(

                    code="INVALID_PHONE_FORMAT",
                    **error_kwargs,
                )

        email = update_data.get("email")

        await self._check_contacts_are_free(
            user_id=user.user_id,
            email=email,
            phone=phone if phone_is_set else None,
            error_kwargs=error_kwargs,
        )

        for field, value in update_data.items():
            setattr(user, field, value)

        if phone_is_set:
            user.phone = phone

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()

            await raise_backend_error(
                code="UPDATE_ME_FAILED",
                **error_kwargs,
            )

        await self.db.refresh(user)

        return await self.get_me(
            current_user=current_user,
        )

    async def _check_contacts_are_free(
        self,
        *,
        user_id: int,
        email: str | None,
        phone: str | None,
        error_kwargs: dict,
    ) -> None:
        """Проверяет, что email и телефон не заняты другим пользователем.

        None означает, что значение не задано и проверять нечего:
        поле не передавалось или было очищено до пустоты.
        """
        if phone is not None:
            phone_taken = await self._is_contact_taken(
                User.phone == phone,
                user_id=user_id,
            )

            if phone_taken:
                await raise_backend_error(
                    code="PHONE_ALREADY_EXISTS",
                    **error_kwargs,
                )

        if email is not None:
            email_taken = await self._is_contact_taken(
                User.email == email,
                user_id=user_id,
            )

            if email_taken:
                await raise_backend_error(
                    code="EMAIL_ALREADY_EXISTS",
                    **error_kwargs,
                )

    async def _is_contact_taken(
        self,
        condition: ColumnElement[bool],
        *,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(User.user_id)
            .where(
                condition,
                User.user_id != user_id,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None