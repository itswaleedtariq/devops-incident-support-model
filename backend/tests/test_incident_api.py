"""HTTP contract tests for the incident router using in-memory dependencies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.incidents import router
from app.core.permissions import Role as RoleName
from app.dependencies.current_user import get_current_active_user
from app.dependencies.services import get_incident_service
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.role import Role
from app.models.user import User
from app.services.incident_service import IncidentService


class FakeIncidentRepo:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Incident] = {}

    async def create(self, **fields: Any) -> Incident:
        item = Incident(**fields)
        now = datetime.now(timezone.utc)
        item.created_at = now
        item.updated_at = now
        item.is_deleted = False
        item.deleted_at = None
        self.items[item.id] = item
        return item

    async def get_active(self, incident_id: uuid.UUID) -> Incident | None:
        item = self.items.get(incident_id)
        return item if item and not item.is_deleted else None

    async def update(self, item: Incident, **fields: Any) -> Incident:
        for key, value in fields.items():
            setattr(item, key, value)
        item.updated_at = datetime.now(timezone.utc)
        return item

    async def soft_delete(self, item: Incident) -> Incident:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        return item

    async def paginate_incidents(self, *, created_by=None, status=None, severity=None, search=None, environment=None, offset=0, limit=20, **kwargs):
        items = [item for item in self.items.values() if not item.is_deleted]
        if created_by is not None:
            items = [item for item in items if item.created_by == created_by]
        if status is not None:
            items = [item for item in items if item.status == status]
        if severity is not None:
            items = [item for item in items if item.severity == severity]
        if environment:
            items = [item for item in items if item.environment == environment]
        if search:
            needle = search.lower()
            items = [item for item in items if needle in item.title.lower()]
        return items[offset:offset + limit], len(items)


def make_user(role_name: str) -> User:
    role = Role(name=role_name, description="test")
    role.id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(), full_name="Test Engineer", username="engineer",
        email="engineer@example.com", password_hash="hash", role_id=role.id,
        is_active=True, is_verified=True,
    )
    user.role = role
    user.is_deleted = False
    return user


def make_client(role_name: str = RoleName.DEVOPS_ENGINEER) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    user = make_user(role_name)
    service = IncidentService(FakeIncidentRepo())  # type: ignore[arg-type]
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_incident_service] = lambda: service
    return TestClient(app)


def test_incident_crud_flow() -> None:
    with make_client() as client:
        created = client.post(
            "/api/v1/incidents",
            json={
                "title": "Docker startup failure",
                "description": "The web container exits immediately during startup.",
                "logs": "permission denied",
                "severity": "high",
            },
        )
        assert created.status_code == 201, created.text
        incident_id = created.json()["data"]["id"]

        listed = client.get("/api/v1/incidents?severity=high&search=Docker")
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1

        updated = client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"environment": "production"},
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["environment"] == "production"

        status_response = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "in_progress"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["data"]["status"] == IncidentStatus.IN_PROGRESS.value


def test_viewer_cannot_create_incident() -> None:
    with make_client(RoleName.VIEWER) as client:
        response = client.post(
            "/api/v1/incidents",
            json={"title": "Blocked action", "description": "A viewer must not create an incident."},
        )
        assert response.status_code == 403


def test_only_admin_can_delete_incident() -> None:
    with make_client(RoleName.DEVOPS_ENGINEER) as client:
        created = client.post(
            "/api/v1/incidents",
            json={"title": "Delete permission", "description": "An engineer owns this incident but cannot delete it."},
        )
        incident_id = created.json()["data"]["id"]
        assert client.delete(f"/api/v1/incidents/{incident_id}").status_code == 403


def test_admin_can_soft_delete_incident() -> None:
    with make_client(RoleName.ADMIN) as client:
        created = client.post(
            "/api/v1/incidents",
            json={"title": "Admin deletion", "description": "An administrator can soft-delete this incident record."},
        )
        incident_id = created.json()["data"]["id"]
        deleted = client.delete(f"/api/v1/incidents/{incident_id}")
        assert deleted.status_code == 200
        assert client.get(f"/api/v1/incidents/{incident_id}").status_code == 404


def test_invalid_sort_field_is_rejected() -> None:
    with make_client() as client:
        response = client.get("/api/v1/incidents?sort_by=created_by")
        assert response.status_code == 400
