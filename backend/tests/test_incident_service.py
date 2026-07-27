"""Unit tests for incident business rules without a database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest

from app.core.permissions import Role as RoleName
from app.exceptions import DomainValidationError, NotFoundError
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.role import Role
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentStatusUpdate, IncidentUpdate
from app.services.incident_service import IncidentService


class FakeIncidentRepository:
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
        return item if item is not None and not item.is_deleted else None

    async def update(self, item: Incident, **fields: Any) -> Incident:
        for key, value in fields.items():
            setattr(item, key, value)
        item.updated_at = datetime.now(timezone.utc)
        return item

    async def soft_delete(self, item: Incident) -> Incident:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        return item

    async def paginate_incidents(self, *, created_by=None, status=None, severity=None, search=None, offset=0, limit=20, **kwargs):
        items = [item for item in self.items.values() if not item.is_deleted]
        if created_by is not None:
            items = [item for item in items if item.created_by == created_by]
        if status is not None:
            items = [item for item in items if item.status == status]
        if severity is not None:
            items = [item for item in items if item.severity == severity]
        if search:
            needle = search.lower()
            items = [item for item in items if needle in item.title.lower() or needle in item.description.lower()]
        return items[offset:offset + limit], len(items)


def make_user(role_name: str) -> User:
    role = Role(name=role_name, description="test")
    role.id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(),
        full_name="Engineer",
        username=f"user-{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hash",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    user.role = role
    user.is_deleted = False
    return user


@pytest.mark.asyncio
async def test_create_and_update_incident() -> None:
    repo = FakeIncidentRepository()
    service = IncidentService(repo)  # type: ignore[arg-type]
    user = make_user(RoleName.DEVOPS_ENGINEER)

    incident = await service.create_incident(
        IncidentCreate(
            title="Docker startup failure",
            description="Container exits immediately during startup.",
            logs="permission denied",
            severity=IncidentSeverity.HIGH,
        ),
        user,
    )
    assert incident.created_by == user.id
    assert incident.status is IncidentStatus.OPEN

    updated = await service.update_incident(
        incident.id,
        IncidentUpdate(environment="production"),
        user,
    )
    assert updated.environment == "production"

    changed = await service.update_status(
        incident.id,
        IncidentStatusUpdate(status=IncidentStatus.IN_PROGRESS),
        user,
    )
    assert changed.status is IncidentStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_non_owner_cannot_read_incident() -> None:
    repo = FakeIncidentRepository()
    service = IncidentService(repo)  # type: ignore[arg-type]
    owner = make_user(RoleName.DEVOPS_ENGINEER)
    stranger = make_user(RoleName.DEVOPS_ENGINEER)
    incident = await service.create_incident(
        IncidentCreate(title="Nginx failure", description="The upstream is refusing connections."),
        owner,
    )

    with pytest.raises(NotFoundError):
        await service.get_incident(incident.id, stranger)


@pytest.mark.asyncio
async def test_admin_can_view_other_users_incidents() -> None:
    repo = FakeIncidentRepository()
    service = IncidentService(repo)  # type: ignore[arg-type]
    owner = make_user(RoleName.DEVOPS_ENGINEER)
    admin = make_user(RoleName.ADMIN)
    incident = await service.create_incident(
        IncidentCreate(title="Kubernetes failure", description="The API pod is repeatedly restarting."),
        owner,
    )
    assert await service.get_incident(incident.id, admin) is incident


@pytest.mark.asyncio
async def test_empty_update_is_rejected() -> None:
    repo = FakeIncidentRepository()
    service = IncidentService(repo)  # type: ignore[arg-type]
    user = make_user(RoleName.DEVOPS_ENGINEER)
    incident = await service.create_incident(
        IncidentCreate(title="Linux disk issue", description="The service reports no space left on device."),
        user,
    )
    with pytest.raises(DomainValidationError):
        await service.update_incident(incident.id, IncidentUpdate(), user)


@pytest.mark.asyncio
async def test_soft_deleted_incident_is_hidden() -> None:
    repo = FakeIncidentRepository()
    service = IncidentService(repo)  # type: ignore[arg-type]
    admin = make_user(RoleName.ADMIN)
    incident = await service.create_incident(
        IncidentCreate(title="Django error", description="The deployment cannot load the application module."),
        admin,
    )
    await service.delete_incident(incident.id, admin)
    with pytest.raises(NotFoundError):
        await service.get_incident(incident.id, admin)
