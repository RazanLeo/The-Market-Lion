"""Centralized settings — loaded from environment via pydantic-settings."""
from __future__ import annotations

from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "The Market Lion"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    # Auth
    JWT_SECRET: SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRES_MIN: int = 30
    JWT_REFRESH_EXPIRES_DAYS: int = 14
    TWO_FA_ISSUER: str = "The Market Lion"
    ENCRYPTION_KEY: SecretStr

    # DB
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Capital.com
    CAPITAL_BASE_URL: str = "https://api-capital.backend-capital.com"
    CAPITAL_DEMO_BASE_URL: str = "https://demo-api-capital.backend-capital.com"
    CAPITAL_STREAM_URL: str = "https://api-streaming-capital.backend-capital.com"
    CAPITAL_API_KEY: str | None = None
    CAPITAL_API_PASSWORD: SecretStr | None = None
    CAPITAL_IDENTIFIER: str | None = None

    # Exness
    EXNESS_ENABLED: bool = False
    EXNESS_API_KEY: str | None = None
    EXNESS_API_SECRET: SecretStr | None = None

    # Market data
    ALPHA_VANTAGE_KEY: str | None = None
    FMP_KEY: str | None = None
    FRED_API_KEY: str | None = None
    EIA_API_KEY: str | None = None
    NEWSAPI_KEY: str | None = None
    TWITTER_BEARER: SecretStr | None = None
    GDELT_ENABLED: bool = True

    # LLMs
    OPENAI_API_KEY: SecretStr | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None
    HF_TOKEN: SecretStr | None = None

    # Payments
    HYPERPAY_BASE_URL: str = "https://eu-test.oppwa.com"
    HYPERPAY_ACCESS_TOKEN: SecretStr | None = None
    HYPERPAY_ENTITY_ID_MADA: str | None = None
    HYPERPAY_ENTITY_ID_VISA: str | None = None
    STRIPE_SECRET_KEY: SecretStr | None = None
    STRIPE_WEBHOOK_SECRET: SecretStr | None = None
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: SecretStr | None = None
    PAYPAL_WEBHOOK_ID: str | None = None
    PAYTABS_ENABLED: bool = False
    PAYTABS_PROFILE_ID: str | None = None
    PAYTABS_SERVER_KEY: SecretStr | None = None

    # Email
    RESEND_API_KEY: SecretStr | None = None
    EMAIL_FROM: str = "The Market Lion <noreply@marketlion.ai>"
    SUPPORT_EMAIL: str = "support@marketlion.ai"

    # Storage
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: SecretStr | None = None

    # Observability
    SENTRY_DSN: str | None = None

    # Feature flags
    FEATURE_AUTO_TRADING: bool = True
    FEATURE_NEWS_PIPELINE: bool = True
    FEATURE_BOOKMAP: bool = True
    FEATURE_RL_LEARNING: bool = True
    FEATURE_CHAT_AI: bool = True

    # Risk defaults
    DEFAULT_MAX_RISK_PCT: float = 10.0
    DEFAULT_MIN_RISK_PCT: float = 1.0
    DAILY_LOSS_LIMIT_PCT: float = 3.0
    WEEKLY_LOSS_LIMIT_PCT: float = 7.0
    MONTHLY_LOSS_LIMIT_PCT: float = 15.0
    EQUITY_DRAWDOWN_FLOOR_PCT: float = 80.0
    MAX_CONCURRENT_TRADES: int = 5
    CONFLUENCE_THRESHOLD_DEFAULT: float = 80.0


settings = Settings()  # type: ignore[call-arg]
