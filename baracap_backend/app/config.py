from functools import lru_cache

from pydantic import AnyHttpUrl
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/baracap_db"
    JWT_SECRET: str = "baracap_default_secret_replace_with_env_value"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    GOOGLE_CLIENT_ID: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    ADMIN_STATS_TOKEN: str = ""
    SIMPLE_GUIDE_URL: str = ""
    PROFESSIONAL_GUIDE_URL: str = ""
    FRONTEND_URL: AnyHttpUrl | str = "http://127.0.0.1:8000"
    AUTO_CREATE_TABLES: bool = False
    DEV_AUTH_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_async_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            str(self.FRONTEND_URL).rstrip("/"),
            "http://localhost:5173",
            "http://localhost:8080",
        ]
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
