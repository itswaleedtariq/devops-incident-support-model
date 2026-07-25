"""
Application configuration and settings management.

Supports multiple environments: development, testing, production.
Environment is selected via the ``APP_ENV`` environment variable.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Base settings shared across all environments."""

    # Application
    APP_NAME: str = "DevOps Incident Support Model"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered DevOps troubleshooting assistant"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # ------------------------------------------------------------------
    # Database — individual components
    # ------------------------------------------------------------------
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "devops_incident_db"
    DATABASE_USER: str = "devops_user"
    DATABASE_PASSWORD: str = "devops_password"
    # If DATABASE_URL is set it takes precedence over the individual fields.
    DATABASE_URL: str = ""

    # Connection pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800   # seconds — reconnect after 30 min
    DB_ECHO: bool = False          # Log SQL statements
    DB_USE_NULL_POOL: bool = False  # Use NullPool (for testing)

    # ------------------------------------------------------------------
    # Security & JWT
    # ------------------------------------------------------------------
    # WARNING: JWT_SECRET_KEY MUST be overridden via env var in production.
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-A-LONG-RANDOM-STRING"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # bcrypt work factor — 12 is a good balance in 2026.
    BCRYPT_ROUNDS: int = 12
    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # ------------------------------------------------------------------
    # CORS & Trusted Hosts
    # ------------------------------------------------------------------
    # Comma-separated origins.  "*" in dev only.
    CORS_ALLOWED_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    TRUSTED_HOSTS: str = "*"  # Comma-separated; "*" allows any Host header

    # ------------------------------------------------------------------
    # Rate limiting (SlowAPI)
    # ------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_FORGOT_PASSWORD: str = "3/minute"
    RATE_LIMIT_RESET_PASSWORD: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "20/minute"

    # ------------------------------------------------------------------
    # Computed URLs (derived from the fields above)
    # ------------------------------------------------------------------
    @computed_field  # type: ignore[misc]
    @property
    def cors_allowed_origins_list(self) -> list[str]:
        """Parse the comma-separated ``CORS_ALLOWED_ORIGINS`` into a list."""
        raw = (self.CORS_ALLOWED_ORIGINS or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def trusted_hosts_list(self) -> list[str]:
        """Parse the comma-separated ``TRUSTED_HOSTS`` into a list."""
        raw = (self.TRUSTED_HOSTS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [h.strip() for h in raw.split(",") if h.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def async_database_url(self) -> str:
        """
        Async SQLAlchemy URL for application runtime (asyncpg driver).

        If ``DATABASE_URL`` is provided it is normalised to use the
        ``postgresql+asyncpg://`` scheme. Otherwise the URL is assembled
        from the individual ``DATABASE_*`` settings.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def sync_database_url(self) -> str:
        """
        Synchronous SQLAlchemy URL for Alembic migrations.

        Alembic does not support asyncpg directly; this URL uses the plain
        ``postgresql://`` scheme which Alembic drives through its own
        connection layer.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if "+asyncpg" in url:
                return url.replace("+asyncpg", "", 1)
            return url
        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


class DevelopmentSettings(BaseAppSettings):
    """Development environment settings."""

    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DB_ECHO: bool = True  # Log SQL in development


class TestingSettings(BaseAppSettings):
    """Testing environment settings."""

    APP_ENV: Literal["development", "testing", "production"] = "testing"
    DEBUG: bool = True
    LOG_LEVEL: str = "WARNING"
    LOG_DIR: str = "logs/test"

    # Use a dedicated test database
    DATABASE_NAME: str = "devops_incident_test_db"

    # Minimise pool overhead during tests
    DB_POOL_SIZE: int = 2
    DB_MAX_OVERFLOW: int = 0
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_RECYCLE: int = 300
    DB_ECHO: bool = False
    DB_USE_NULL_POOL: bool = True   # NullPool — no idle connections in tests


class ProductionSettings(BaseAppSettings):
    """Production environment settings."""

    APP_ENV: Literal["development", "testing", "production"] = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    WORKERS: int = 4

    # Larger pool for production traffic
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False
    DB_USE_NULL_POOL: bool = False


_SETTINGS_MAP: dict[str, type[BaseAppSettings]] = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}


@lru_cache(maxsize=1)
def get_settings() -> BaseAppSettings:
    """
    Return the settings instance for the current environment.

    The instance is cached so the ``.env`` file is read only once per process.
    Clear the cache with ``get_settings.cache_clear()`` in tests that need to
    override environment variables.
    """
    env = os.getenv("APP_ENV", "development")
    settings_class = _SETTINGS_MAP.get(env, DevelopmentSettings)
    return settings_class()


# Module-level singleton used throughout the application.
settings: BaseAppSettings = get_settings()



@lru_cache(maxsize=1)
def get_settings() -> BaseAppSettings:
    """
    Return the settings instance for the current environment.

    The instance is cached so the ``.env`` file is read only once per process.
    Clear the cache with ``get_settings.cache_clear()`` in tests that need to
    override environment variables.
    """
    env = os.getenv("APP_ENV", "development")
    settings_class = _SETTINGS_MAP.get(env, DevelopmentSettings)
    return settings_class()


# Module-level singleton used throughout the application.
settings: BaseAppSettings = get_settings()
