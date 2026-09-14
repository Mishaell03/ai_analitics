from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import CurrentUserContext
from app.core.minio_url import minio_storage
from app.core.config import settings
from app.api.v1.schemas.users import MeResponse


class UserService:

    async def get_me(
        self,
        db: AsyncSession,
        request: Request,
        current_user: CurrentUserContext,
    ) -> MeResponse:
        user = current_user.user

        img_url = None

        if user.img:
            img_url = await minio_storage.get_url(
                file_path=user.img + ".webp",
                bucket="avatars" if not user.is_default_img else "default-avatars",
                expires=settings.image_url_ttl,
            )

        return MeResponse(
            user_id=user.user_id,
            name=user.name,
            phone=user.phone,
            email=user.email,
            img=img_url,
            is_default_img=user.is_default_img,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


user_service = UserService()