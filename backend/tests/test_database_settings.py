"""
Tests for database settings and URL construction.

These tests validate that the ``pydantic-settings`` configuration correctly
builds async/sync connection URLs and applies sensible defaults for the
testing environment.  No live database is required.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _use_testing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure testing settings are active for every test in this module."""
    monkeypatch.setenv("APP_ENV", "testing")


def _fresh_settings():
    """Return a fresh (uncached) settings instance."""
    from app.config.settings import get_settings

    get_settings.cache_clear()
    s = get_settings()
    get_settings.cache_clear()  # Leave the cache clean for other tests
    return s


class TestDatabaseURLConstruction:
    """Verify that computed URLs are built correctly from individual fields."""

    def test_async_url_uses_asyncpg_scheme(self) -> None:
        s = _fresh_settings()
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_sync_url_uses_plain_postgresql_scheme(self) -> None:
        s = _fresh_settings()
        assert s.sync_database_url.startswith("postgresql://")
        assert "+asyncpg" not in s.sync_database_url

    def test_async_url_contains_host(self) -> None:
        s = _fresh_settings()
        assert s.DATABASE_HOST in s.async_database_url

    def test_async_url_contains_port(self) -> None:
        s = _fresh_settings()
        assert str(s.DATABASE_PORT) in s.async_database_url

    def test_async_url_contains_db_name(self) -> None:
        s = _fresh_settings()
        assert s.DATABASE_NAME in s.async_database_url

    def test_database_url_override_normalised_to_asyncpg(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A plain ``postgresql://`` DATABASE_URL should be normalised."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/mydb")
        s = _fresh_settings()
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_database_url_override_sync_strips_asyncpg(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/mydb"
        )
        s = _fresh_settings()
        assert "+asyncpg" not in s.sync_database_url


class TestDatabaseDefaults:
    """Verify default values match documentation."""

    def test_default_port(self) -> None:
        s = _fresh_settings()
        assert s.DATABASE_PORT == 5432

    def test_testing_env_uses_test_db_name(self) -> None:
        s = _fresh_settings()
        assert "test" in s.DATABASE_NAME.lower()

    def test_testing_env_uses_null_pool(self) -> None:
        s = _fresh_settings()
        assert s.DB_USE_NULL_POOL is True

    def test_pool_size_is_positive(self) -> None:
        s = _fresh_settings()
        assert s.DB_POOL_SIZE >= 1

    def test_pool_timeout_is_positive(self) -> None:
        s = _fresh_settings()
        assert s.DB_POOL_TIMEOUT > 0

    def test_pool_recycle_is_positive(self) -> None:
        s = _fresh_settings()
        assert s.DB_POOL_RECYCLE > 0
