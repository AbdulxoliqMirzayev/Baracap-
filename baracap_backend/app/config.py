import os
from functools import lru_cache

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
    FRONTEND_URL: str = "http://127.0.0.1:8000"
    PUBLIC_DOMAIN: str = ""
    CUSTOM_DOMAIN: str = ""
    CORS_ORIGINS: str = ""
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

    @staticmethod
    def normalize_origin(value: str) -> str:
        value = value.strip().rstrip("/")
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("//"):
            return f"https:{value}"
        return f"https://{value}"

    @property
    def public_frontend_url(self) -> str:
        deployment_candidates = [
            self.PUBLIC_DOMAIN,
            self.CUSTOM_DOMAIN,
            os.getenv("RAILWAY_PUBLIC_DOMAIN", ""),
            os.getenv("RAILWAY_STATIC_URL", ""),
        ]
        for candidate in deployment_candidates:
            origin = self.normalize_origin(candidate)
            if origin:
                return origin

        frontend_origin = self.normalize_origin(str(self.FRONTEND_URL))
        if frontend_origin:
            return frontend_origin

        return "http://127.0.0.1:8000"

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            self.public_frontend_url,
            self.normalize_origin(self.PUBLIC_DOMAIN),
            self.normalize_origin(self.CUSTOM_DOMAIN),
            self.normalize_origin(os.getenv("RAILWAY_PUBLIC_DOMAIN", "")),
            self.normalize_origin(os.getenv("RAILWAY_STATIC_URL", "")),
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
        origins.extend(
            self.normalize_origin(origin)
            for origin in self.CORS_ORIGINS.split(",")
        )
        return list(dict.fromkeys(origin for origin in origins if origin))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
