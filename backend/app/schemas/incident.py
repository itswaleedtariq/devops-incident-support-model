"""Pydantic schemas for incident management APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import IncidentSeverity, IncidentStatus


class IncidentCreate(BaseModel):
    """Payload for creating a new incident."""

    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10, max_length=20_000)
    environment: str | None = Field(default=None, max_length=100)
    logs: str | None = Field(default=None, max_length=200_000)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM

    @field_validator("title", "description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank.")
        return cleaned

    @field_validator("environment", "logs")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class IncidentUpdate(BaseModel):
    """Partial incident update. Status is changed through the status endpoint."""

    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = Field(default=None, min_length=10, max_length=20_000)
    environment: str | None = Field(default=None, max_length=100)
    logs: str | None = Field(default=None, max_length=200_000)
    severity: IncidentSeverity | None = None

    @field_validator("title", "description")
    @classmethod
    def strip_nonblank_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank.")
        return cleaned

    @field_validator("environment", "logs")
    @classmethod
    def strip_nullable_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class IncidentStatusUpdate(BaseModel):
    """Payload for changing only the workflow status."""

    status: IncidentStatus


class IncidentRead(BaseModel):
    """Public incident representation returned by the API."""

    id: uuid.UUID
    title: str
    description: str
    environment: str | None
    logs: str | None
    status: IncidentStatus
    severity: IncidentSeverity
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
