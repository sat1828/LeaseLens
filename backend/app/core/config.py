from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # App
    APP_NAME: str = "LeaseLens"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-this-in-production-minimum-32-characters"
    FRONTEND_URL: str = "http://localhost:5173"
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/leaselens"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/leaselens"

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic AI
    ANTHROPIC_API_KEY: str = ""

    # Stripe (optional — leave blank until you're ready to charge)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_TEAM_PRICE_ID: str = ""

    # Email (optional)
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "hello@leaselens.in"

    # Security
    FIELD_ENCRYPTION_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Limits
    FREE_ANALYSES_PER_MONTH: int = 1
    PRO_ANALYSES_PER_MONTH: int = 999999
    MAX_PDF_SIZE_MB: int = 25
    MAX_PDF_PAGES: int = 100

    # Features
    ENABLE_OCR: bool = True
    ENABLE_RAG: bool = False
    RAG_TOP_K: int = 15


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
