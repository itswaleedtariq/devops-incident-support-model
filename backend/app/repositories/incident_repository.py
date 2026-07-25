"""Incident repository."""

from __future__ import annotations

from app.models.incident import Incident
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    """Data-access operations for the :class:`~app.models.incident.Incident` model."""

    model = Incident
