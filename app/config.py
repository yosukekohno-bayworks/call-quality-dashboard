from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "Call Quality Dashboard API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/call_quality_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Cloud Storage
    GCS_BUCKET_NAME: str = ""
    GCS_PROJECT_ID: str = ""

    # OpenAI (Whisper)
    OPENAI_API_KEY: str = ""

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str = ""

    # Hume AI
    HUME_API_KEY: str = ""

    # Biztel API (default values, overridden per tenant)
    BIZTEL_API_TIMEOUT: int = 30
    BIZTEL_API_RATE_LIMIT_DELAY: float = 0.1  # 100ms between requests


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
