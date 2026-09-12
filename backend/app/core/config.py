import os
from ipaddress import ip_network
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
load_dotenv()

class Settings:
    # DATABASE
    db_host: str = os.getenv("DB_HOST")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME")
    db_user: str = os.getenv("DB_USER")
    db_password: str = os.getenv("DB_PASSWORD")

    # API
    api_reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"

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