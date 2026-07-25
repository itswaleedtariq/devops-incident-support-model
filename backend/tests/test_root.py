"""
Tests for the root endpoint.

Route: GET /
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test suite for GET /."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_content_type_is_json(self, client: TestClient) -> None:
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]

    def test_response_envelope_shape(self, client: TestClient) -> None:
        body = client.get("/").json()
        assert "success" in body
        assert "message" in body
        assert "data" in body

    def test_success_is_true(self, client: TestClient) -> None:
        body = client.get("/").json()
        assert body["success"] is True

    def test_data_contains_application_name(self, client: TestClient) -> None:
        data = client.get("/").json()["data"]
        assert data["application"] == "DevOps Incident Support Model"

    def test_data_contains_running_status(self, client: TestClient) -> None:
        data = client.get("/").json()["data"]
        assert data["status"] == "running"
