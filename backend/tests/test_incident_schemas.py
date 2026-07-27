"""Validation tests for incident API schemas."""

import pytest
from pydantic import ValidationError

from app.models.enums import IncidentSeverity
from app.schemas.incident import IncidentCreate, IncidentUpdate


def test_create_schema_trims_text() -> None:
    payload = IncidentCreate(
        title="  Docker failure  ",
        description="  The container exits during application startup.  ",
        environment=" production ",
        severity=IncidentSeverity.HIGH,
    )
    assert payload.title == "Docker failure"
    assert payload.description == "The container exits during application startup."
    assert payload.environment == "production"


def test_create_schema_rejects_blank_required_text() -> None:
    with pytest.raises(ValidationError):
        IncidentCreate(title="   ", description="A sufficiently long description.")


def test_update_schema_allows_clearing_optional_fields() -> None:
    payload = IncidentUpdate(environment=None, logs=None)
    assert payload.model_dump(exclude_unset=True) == {"environment": None, "logs": None}
