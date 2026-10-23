import logging
import os
from ipaddress import ip_network
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio

logger = logging.getLogger(__name__)

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

    # переносить ли старые объекты в раскладку course-content при старте
    minio_migrate_on_startup: bool = (
        os.getenv("MINIO_MIGRATE_ON_STARTUP", "true").lower() == "true"
    )


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

    # максимальный размер стандартного тела запроса (JSON/Form) - 10 МБ
    max_standard_body_size: int = int(
        os.getenv("MAX_STANDARD_BODY_SIZE", "10485760")
    )

    # MEDIA
    # файлы курсов лежат в одном баке course-content и отдаются
    # только по presigned URL
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
    @staticmethod
    def _parse_trusted_proxies(raw: str | None) -> list:
        default_proxies = ["127.0.0.0/8", "::1/128"]
        if not raw or not raw.strip():
            return [ip_network(net) for net in default_proxies]
        networks = []
        for item in raw.split(","):
            trimmed = item.strip()
            if not trimmed:
                continue
            try:
                networks.append(ip_network(trimmed, strict=False))
            except ValueError:
                logging.getLogger(__name__).warning(
                    f"Invalid network in TRUSTED_PROXIES: {trimmed}"
                )
        return networks or [ip_network(net) for net in default_proxies]

    trusted_proxies: list = _parse_trusted_proxies(os.getenv("TRUSTED_PROXIES"))
    geoip_db_path: str = os.getenv("GEOIP_DB_PATH")

    # CORS/CSRF
    # домены фронтенда через запятую; пусто - работает только localhost-regex
    cors_origins: tuple[str, ...] = tuple(
        item.strip().rstrip("/")
        for item in os.getenv("CORS_ORIGINS", "").split(",")
        if item.strip()
    )

    # SESSIONS
    session_ttl_days: int = int(os.getenv("SESSION_TTL_DAYS", "180"))
    session_cookie_secure: bool = (
        os.getenv("SESSION_COOKIE_SECURE", str(is_product)).lower() == "true"
    )
    session_cookie_samesite: str = os.getenv(
        "SESSION_COOKIE_SAMESITE",
        "none" if is_product else "lax",
    ).lower()
    if session_cookie_samesite not in {"lax", "strict", "none"}:
        session_cookie_samesite = "lax"

    # Браузеры отклоняют SameSite=None без Secure
    if session_cookie_samesite == "none" and not session_cookie_secure:
        session_cookie_secure = True

    # RATE LIMIT (запросы с одного IP за окно)
    auth_rate_limit_enabled: bool = (
        os.getenv("AUTH_RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    auth_login_rate_limit: int = int(os.getenv("AUTH_LOGIN_RATE_LIMIT", "10"))
    auth_register_rate_limit: int = int(os.getenv("AUTH_REGISTER_RATE_LIMIT", "5"))
    auth_rate_limit_window_seconds: int = int(
        os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")
    )

    # MINIO
    # сколько presign-запросов выполняем одновременно
    minio_presign_concurrency: int = int(
        os.getenv("MINIO_PRESIGN_CONCURRENCY", "10")
    )

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
