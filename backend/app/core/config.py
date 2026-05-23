from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Manpower Management Platform"
    DEBUG: bool = True

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://manpower:manpower@localhost:5432/manpower",
        description="Async SQLAlchemy DSN",
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8

    UPLOAD_DIR: str = "./uploads"
    UPLOAD_MAX_MB: int = 32

    COCKPIT_ALLOWED_IPS: str = "127.0.0.1,::1"
    COCKPIT_TOKEN: str = "cockpit-dev-token"

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
