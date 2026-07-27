"""Incident-specific data-access operations."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import Select, func, or_, select

from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    """Repository for active and historical incident records."""

    model = Incident

    async def get_active(self, incident_id: uuid.UUID) -> Incident | None:
        """Return a non-deleted incident by ID."""
        stmt = select(Incident).where(
            Incident.id == incident_id,
            Incident.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def paginate_incidents(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str | None = None,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        environment: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> tuple[list[Incident], int]:
        """List active incidents with search, filtering, sorting and pagination."""
        clauses = [Incident.is_deleted.is_(False)]

        if status is not None:
            clauses.append(Incident.status == status)
        if severity is not None:
            clauses.append(Incident.severity == severity)
        if environment:
            clauses.append(Incident.environment.ilike(environment.strip()))
        if created_by is not None:
            clauses.append(Incident.created_by == created_by)

        stmt: Select = select(Incident).where(*clauses)
        count_stmt: Select = select(func.count()).select_from(Incident).where(*clauses)

        if search:
            pattern = f"%{search.strip()}%"
            search_clause = or_(
                Incident.title.ilike(pattern),
                Incident.description.ilike(pattern),
                Incident.logs.ilike(pattern),
                Incident.environment.ilike(pattern),
            )
            stmt = stmt.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        sortable: Sequence[str] = (
            "created_at",
            "updated_at",
            "title",
            "status",
            "severity",
            "environment",
        )
        effective_sort = sort_by if sort_by in sortable else "created_at"
        column = getattr(Incident, effective_sort)
        stmt = stmt.order_by(column.asc() if sort_order == "asc" else column.desc())
        stmt = stmt.offset(offset).limit(limit)

        items_result = await self.session.execute(stmt)
        total_result = await self.session.execute(count_stmt)
        return list(items_result.scalars().all()), int(total_result.scalar_one() or 0)
