from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Market Lion API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/market_lion"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change-me-in-production-super-secret-key-market-lion-2025"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # Capital.com
    CAPITAL_COM_API_KEY: Optional[str] = None
    CAPITAL_COM_IDENTIFIER: Optional[str] = None
    CAPITAL_COM_PASSWORD: Optional[str] = None
    CAPITAL_COM_DEMO: bool = True

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # News / Fundamental
    ALPHA_VANTAGE_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
