from app.core import session
from app.core.session import CurrentUserContext
from app.core.minio_url import minio_storage
from app.core.config import settings
from app.api.v1.schemas.users import MeResponse


class UserService:

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
            expires_at=session.expires_at
        )


user_service = UserService()