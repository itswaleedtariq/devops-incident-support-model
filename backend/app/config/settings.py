"""
Application configuration and settings management.

Supports multiple environments: development, testing, production.
Environment is selected via the ``APP_ENV`` environment variable.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

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


class TestingSettings(BaseAppSettings):
    """Testing environment settings."""

    APP_ENV: Literal["development", "testing", "production"] = "testing"
    DEBUG: bool = True
    LOG_LEVEL: str = "WARNING"
    LOG_DIR: str = "logs/test"


class ProductionSettings(BaseAppSettings):
    """Production environment settings."""

    APP_ENV: Literal["development", "testing", "production"] = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    WORKERS: int = 4


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
