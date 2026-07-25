"""
Tests for the health endpoint with explicit database connectivity states.

These tests override the ``db_manager.ping`` mock set up in ``conftest.py``
to verify the endpoint's behaviour when the database is both reachable and
unreachable.  No live PostgreSQL instance is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestHealthWithDatabaseConnected:
    """Health endpoint when database ping returns ``True``."""

    def test_status_is_healthy(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=True),
        ):
            data = client.get("/api/v1/health").json()["data"]
        assert data["status"] == "healthy"

    def test_database_field_is_connected(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=True),
        ):
            data = client.get("/api/v1/health").json()["data"]
        assert data["database"] == "connected"

    def test_version_present(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=True),
        ):
            data = client.get("/api/v1/health").json()["data"]
        assert "version" in data

    def test_http_200(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=True),
        ):
            response = client.get("/api/v1/health")
        assert response.status_code == 200


class TestHealthWithDatabaseDisconnected:
    """Health endpoint when database ping returns ``False``."""

    def test_http_still_200(self, client: TestClient) -> None:
        """A degraded service still returns HTTP 200 — not a server error."""
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=False),
        ):
            response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_status_is_degraded(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=False),
        ):
            data = client.get("/api/v1/health").json()["data"]
        assert data["status"] == "degraded"

    def test_database_field_is_disconnected(self, client: TestClient) -> None:
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=False),
        ):
            data = client.get("/api/v1/health").json()["data"]
        assert data["database"] == "disconnected"

    def test_success_envelope_is_still_true(self, client: TestClient) -> None:
        """The envelope ``success`` field reflects HTTP-level success, not DB health."""
        with patch(
            "app.database.database.db_manager.ping",
            new=AsyncMock(return_value=False),
        ):
            body = client.get("/api/v1/health").json()
        assert body["success"] is True
