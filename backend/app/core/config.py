import os
from ipaddress import ip_network
from pathlib import Path
from dotenv import load_dotenv

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
    api_reload: bool = os.getenv("API_RELOAD", False)

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