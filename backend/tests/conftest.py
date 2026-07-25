"""
Pytest configuration and shared fixtures.

Fixtures defined here are available to every test in the suite without
explicit import — Pytest discovers ``conftest.py`` automatically.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Force testing settings before importing the app.
os.environ.setdefault("APP_ENV", "testing")


# ---------------------------------------------------------------------------
# Integration-test gating
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--integration`` CLI flag."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require a live PostgreSQL database.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ``pytest.mark.integration`` tests unless ``--integration`` is passed."""
    if config.getoption("--integration"):
        return  # user explicitly opted in — run everything

    skip_marker = pytest.mark.skip(
        reason="Integration test skipped. Pass --integration to run."
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Provide a synchronous ``TestClient`` for the full application.

    Session scope: the app is created once per pytest session, which is
    faster and mirrors real production behaviour more closely.

    The database ``ping`` is mocked so unit tests do not require a live
    PostgreSQL instance.  Use the ``db_integration`` mark for tests that
    need a real database.
    """
    # Import here to ensure APP_ENV is set first
    from app.config.settings import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    application = create_app()

    # Patch db_manager.ping so the health endpoint reports "healthy"
    # without a live database during unit tests.
    with patch(
        "app.database.database.db_manager.ping",
        new=AsyncMock(return_value=True),
    ):
        with TestClient(application, raise_server_exceptions=False) as test_client:
            yield test_client
