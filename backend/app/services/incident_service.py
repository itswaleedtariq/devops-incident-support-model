"""Business logic for incident creation, history, updates and deletion."""

from __future__ import annotations

import uuid

from app.exceptions import DomainValidationError, NotFoundError
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.user import User
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentStatusUpdate, IncidentUpdate
from app.services.permission_service import PermissionService


class IncidentService:
    """Coordinates incident rules independently of the HTTP layer."""

    def __init__(self, incident_repo: IncidentRepository) -> None:
        self.incident_repo = incident_repo

    @staticmethod
    def _can_access(user: User, incident: Incident) -> bool:
        """Admins can access all incidents; other users can access their own."""
        return PermissionService.is_admin(user) or incident.created_by == user.id

    async def create_incident(self, payload: IncidentCreate, user: User) -> Incident:
        """Create an open incident owned by the authenticated user."""
        return await self.incident_repo.create(
            id=uuid.uuid4(),
            title=payload.title,
            description=payload.description,
            environment=payload.environment,
            logs=payload.logs,
            status=IncidentStatus.OPEN,
            severity=payload.severity,
            created_by=user.id,
        )

    async def get_incident(self, incident_id: uuid.UUID, user: User) -> Incident:
        """Return a visible incident or raise NotFoundError."""
        incident = await self.incident_repo.get_active(incident_id)
        if incident is None or not self._can_access(user, incident):
            # A 404 avoids exposing the existence of another user's incident.
            raise NotFoundError(f"Incident {incident_id} not found.")
        return incident

    async def list_incidents(
        self,
        *,
        user: User,
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        search: str | None,
        status: IncidentStatus | None,
        severity: IncidentSeverity | None,
        environment: str | None,
    ) -> tuple[list[Incident], int]:
        """Return the user's incident history; admins receive the full history."""
        owner_id = None if PermissionService.is_admin(user) else user.id
        return await self.incident_repo.paginate_incidents(
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            status=status,
            severity=severity,
            environment=environment,
            created_by=owner_id,
        )

    async def update_incident(
        self,
        incident_id: uuid.UUID,
        payload: IncidentUpdate,
        user: User,
    ) -> Incident:
        """Update editable incident details."""
        incident = await self.get_incident(incident_id, user)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise DomainValidationError("At least one incident field must be provided.")
        return await self.incident_repo.update(incident, **updates)

    async def update_status(
        self,
        incident_id: uuid.UUID,
        payload: IncidentStatusUpdate,
        user: User,
    ) -> Incident:
        """Change the incident workflow status."""
        incident = await self.get_incident(incident_id, user)
        if incident.status == payload.status:
            return incident
        return await self.incident_repo.update(incident, status=payload.status)

    async def delete_incident(self, incident_id: uuid.UUID, user: User) -> Incident:
        """Soft-delete an incident so its audit history remains available."""
        incident = await self.get_incident(incident_id, user)
        return await self.incident_repo.soft_delete(incident)
