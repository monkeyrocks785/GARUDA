from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "GARUDA"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    WORKERS: int = 1

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'garuda.db'}"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = str(BASE_DIR / "storage" / "logs")

    # Storage
    STORAGE_DIR: str = str(BASE_DIR / "storage")
    CACHE_DIR: str = str(BASE_DIR / "storage" / "cache")
    TEMP_DIR: str = str(BASE_DIR / "storage" / "temp")
    EXPORT_DIR: str = str(BASE_DIR / "storage" / "exports")
    PROJECTS_DIR: str = str(BASE_DIR / "storage" / "projects")
    MODELS_DIR: str = str(BASE_DIR / "storage" / "models")

    # Offline GIS sources
    TILES_DIR: str = str(BASE_DIR / "storage" / "tiles")
    BASEMAPS_DIR: str = str(BASE_DIR / "storage" / "basemaps")

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
