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
# Use a deterministic JWT secret so signed tokens are reproducible across tests.
os.environ.setdefault(
    "JWT_SECRET_KEY", "unit-test-secret-key-please-do-not-use-in-production"
)


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

    The database ``ping`` is mocked so unit tests do not require a live
    PostgreSQL instance.  Rate limiting is disabled to avoid HTTP 429
    responses during rapid test bursts.
    """
    from app.config.settings import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    application = create_app()

    # Disable SlowAPI limiter for unit tests.
    if hasattr(application.state, "limiter"):
        application.state.limiter.enabled = False

    with patch(
        "app.database.database.db_manager.ping",
        new=AsyncMock(return_value=True),
    ):
        with TestClient(application, raise_server_exceptions=False) as test_client:
            yield test_client
