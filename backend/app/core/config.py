import os
from ipaddress import ip_network
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

class Settings:
    # DATABASE
    db_host: str = os.getenv("DB_HOST")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME")
    db_user: str = os.getenv("DB_USER")
    db_password: str = os.getenv("DB_PASSWORD")

    # API
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    is_product: bool = os.getenv("IS_PRODUCT", "false").lower() == "true"

    # MINIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"


    minio_client = Minio(
        endpoint=minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=minio_secure,
    )

    image_url_ttl: int = int(os.getenv("IMAGE_URL_TTL", "3600"))
    content_url_ttl: int = int(os.getenv("CONTENT_URL_TTL", "3600"))
    video_url_ttl: int = int(os.getenv("VIDEO_URL_TTL", "7200"))
    upload_url_ttl: int = int(os.getenv("UPLOAD_URL_TTL", "900"))

    # максимальный размер текстового файла, который читаем из MinIO
    max_text_file_size: int = int(os.getenv("MAX_TEXT_FILE_SIZE", "1048576"))

    # максимальный размер Markdown урока, который можно загрузить (500 КБ)
    lesson_content_max_upload_size: int = int(
        os.getenv("LESSON_CONTENT_MAX_UPLOAD_SIZE", "512000")
    )

    # MEDIA
    # бак с медиафайлами: приватный, файлы отдаются только по presigned URL
    media_bucket: str = os.getenv("MEDIA_BUCKET", "course-media")

    # срок действия ссылки на файл
    media_url_ttl: int = int(os.getenv("MEDIA_URL_TTL", "600"))

    # максимальный размер загружаемого изображения (10 МБ)
    media_max_image_size: int = int(os.getenv("MEDIA_MAX_IMAGE_SIZE", "10485760"))

    # максимальный размер загружаемого видео (200 МБ)
    media_max_video_size: int = int(os.getenv("MEDIA_MAX_VIDEO_SIZE", "209715200"))

    # максимальная сторона изображения в пикселях
    media_max_image_dimension: int = int(os.getenv("MEDIA_MAX_IMAGE_DIMENSION", "6000"))

    # максимальная сторона видео в пикселях
    media_max_video_dimension: int = int(os.getenv("MEDIA_MAX_VIDEO_DIMENSION", "4096"))

    # качество конвертации в WebP
    media_image_quality: int = int(os.getenv("MEDIA_IMAGE_QUALITY", "82"))

    # максимальное количество пикселей изображения (защита от bomb-файлов)
    media_max_image_pixels: int = int(os.getenv("MEDIA_MAX_IMAGE_PIXELS", "40000000"))

    # допустимые MIME-типы файлов
    media_allowed_image_types: frozenset[str] = frozenset(
        item.strip().lower()
        for item in os.getenv(
            "MEDIA_ALLOWED_IMAGE_TYPES",
            "image/jpeg,image/png,image/webp,image/gif,image/bmp",
        ).split(",")
        if item.strip()
    )

    media_allowed_video_types: frozenset[str] = frozenset(
        item.strip().lower()
        for item in os.getenv(
            "MEDIA_ALLOWED_VIDEO_TYPES",
            "video/mp4",
        ).split(",")
        if item.strip()
    )

    # IP
    trusted_proxies: list = [
        ip_network(network.strip())
        for network in os.getenv(
            "TRUSTED_PROXIES"
        ).split(",")
    ]
    geoip_db_path: str = os.getenv("GEOIP_DB_PATH")

    # DATABASE URL
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}"
            f"/{self.db_name}"
        )

settings = Settings()