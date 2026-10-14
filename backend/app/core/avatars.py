from app.core.config import settings
from app.core.minio_url import minio_storage


# загруженные пользователем аватары и дефолтные
AVATARS_BUCKET = "avatars"
DEFAULT_AVATARS_BUCKET = "default-avatars"

# путь аватара хранится без расширения, в баке он всегда .webp
AVATAR_EXTENSION = ".webp"


async def get_avatar_url(
    img: str | None,
    is_default_img: bool,
) -> str | None:
    """ПОДПИСАННАЯ ССЫЛКА НА АВАТАР ПОЛЬЗОВАТЕЛЯ

    None, если аватара нет или объекта больше нет в баке.
    Фронт сам качает картинку по этой ссылке и кэширует
    по стабильному ключу из пути.
    """

    if not img:
        return None

    return await minio_storage.get_url(
        file_path=img + AVATAR_EXTENSION,
        bucket=DEFAULT_AVATARS_BUCKET if is_default_img else AVATARS_BUCKET,
        expires=settings.image_url_ttl,
    )
