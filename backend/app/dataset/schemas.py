"""Strongly typed schema for DevOps incident fine-tuning records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class IncidentCategory(StrEnum):
    DOCKER = "docker"
    GITHUB_ACTIONS = "github_actions"
    LINUX = "linux"
    NGINX = "nginx"
    GUNICORN = "gunicorn"
    KUBERNETES = "kubernetes"
    DJANGO = "django"


class DatasetRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(StrEnum):
    DIAGNOSTIC = "diagnostic"
    MODIFICATION = "modification"
    VERIFICATION = "verification"


class SourceType(StrEnum):
    MANUAL = "manual"
    SYNTHETIC = "synthetic"
    PUBLIC_DOCUMENTATION = "public_documentation"
    PUBLIC_ISSUE = "public_issue"
    INTERNAL_INCIDENT = "internal_incident"


class DatasetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: str = Field(..., min_length=2, max_length=500)
    incident_description: str = Field(..., min_length=10, max_length=20_000)
    logs: str = Field(..., min_length=3, max_length=200_000)
    recent_changes: str | None = Field(default=None, max_length=10_000)
    expected_behavior: str | None = Field(default=None, max_length=10_000)
    commands_already_tried: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("environment", "incident_description", "logs")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank.")
        return cleaned

    @field_validator("recent_changes", "expected_behavior")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class RecommendedStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str | None = Field(default=None, max_length=5_000)
    purpose: str = Field(..., min_length=5, max_length=2_000)
    action_type: ActionType
    risk: DatasetRiskLevel
    requires_confirmation: bool = False
    warning: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def validate_risky_step(self) -> "RecommendedStep":
        if self.risk in {DatasetRiskLevel.HIGH, DatasetRiskLevel.CRITICAL}:
            if not self.requires_confirmation:
                raise ValueError("High and critical-risk steps must require confirmation.")
            if not self.warning:
                raise ValueError("High and critical-risk steps must include a warning.")
        return self


class DatasetOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_category: IncidentCategory
    probable_causes: list[str] = Field(..., min_length=1, max_length=10)
    evidence: list[str] = Field(..., min_length=1, max_length=20)
    recommended_steps: list[RecommendedStep] = Field(..., min_length=1, max_length=20)
    risk_level: DatasetRiskLevel
    verification_steps: list[str] = Field(..., min_length=1, max_length=20)
    confidence: float = Field(..., ge=0.0, le=1.0)
    missing_information: list[str] = Field(default_factory=list, max_length=20)


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    source_url: HttpUrl | None = None
    license: str | None = Field(default=None, max_length=200)
    reviewed: bool = False
    tags: list[str] = Field(default_factory=list, max_length=20)


class DatasetRecord(BaseModel):
    """One JSONL record used for supervised fine-tuning and evaluation."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[a-z0-9][a-z0-9_-]{5,99}$")
    instruction: str = Field(..., min_length=20, max_length=2_000)
    input: DatasetInput
    output: DatasetOutput
    metadata: DatasetMetadata
