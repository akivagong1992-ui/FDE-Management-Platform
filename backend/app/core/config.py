from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Manpower Management Platform"
    DEBUG: bool = True

    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./manpower.db",
        description="Async SQLAlchemy DSN. Defaults to SQLite for local demo; use Postgres in prod.",
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8

    # AES-GCM key (base64-urlsafe-encoded 32 bytes). Dev default; CHANGE in prod.
    FIELD_ENCRYPTION_KEY: str = "dev-only-32byte-secret-replace-meXXXXXXXXX="

    UPLOAD_DIR: str = "./uploads"
    UPLOAD_MAX_MB: int = 32

    COCKPIT_ALLOWED_IPS: str = "127.0.0.1,::1"
    COCKPIT_TOKEN: str = "cockpit-dev-token"

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # ── 飞书 / Lark 集成接口位 ─────────────────────────
    # Phase 4 才真接：现在留接口、配置和 stub channel，运行时仅记日志。
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_BOT_WEBHOOK_URL: str = ""
    FEISHU_EVENT_VERIFY_TOKEN: str = ""
    FEISHU_EVENT_ENCRYPT_KEY: str = ""
    NOTIFICATION_CHANNELS: str = "log"  # CSV: log,feishu,email


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
