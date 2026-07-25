"""
Pytest configuration and shared fixtures.

Fixtures defined here are available to every test in the suite without
explicit import — Pytest discovers ``conftest.py`` automatically.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Force testing settings before importing the app
os.environ.setdefault("APP_ENV", "testing")


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Provide a synchronous ``TestClient`` for the full application.

    Session scope: the app is created once per pytest session, which is
    faster and mirrors real production behaviour more closely.
    """
    # Import here to ensure APP_ENV is set first
    from app.config.settings import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    application = create_app()

    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client
