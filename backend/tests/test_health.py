"""
Tests for the health check endpoint.

Route: GET /api/v1/health

Note: the database ``ping`` is mocked in ``conftest.py`` so these tests do
not require a live PostgreSQL instance.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for GET /api/v1/health."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_content_type_is_json(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert "application/json" in response.headers["content-type"]

    def test_response_envelope_shape(self, client: TestClient) -> None:
        body = client.get("/api/v1/health").json()
        assert "success" in body
        assert "message" in body
        assert "data" in body

    def test_success_is_true(self, client: TestClient) -> None:
        body = client.get("/api/v1/health").json()
        assert body["success"] is True

    def test_data_status_is_healthy(self, client: TestClient) -> None:
        data = client.get("/api/v1/health").json()["data"]
        assert data["status"] == "healthy"

    def test_data_contains_version(self, client: TestClient) -> None:
        data = client.get("/api/v1/health").json()["data"]
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_data_database_connected(self, client: TestClient) -> None:
        """Database field should be 'connected' (mock returns True in conftest)."""
        data = client.get("/api/v1/health").json()["data"]
        assert data["database"] == "connected"
