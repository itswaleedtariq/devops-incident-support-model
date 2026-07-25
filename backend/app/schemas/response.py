"""
Standard API response schemas.

Every API endpoint returns one of these models to guarantee a consistent
JSON envelope shape across the entire application:

    {
        "success": true | false,
        "message": "...",
        "data": { ... } | null
    }
"""

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    Unified response envelope for all API endpoints.

    Attributes:
        success: ``True`` on success, ``False`` on error.
        message: Human-readable status description.
        data:    Response payload; ``None`` on error responses.
    """

    success: bool
    message: str
    data: Optional[T] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Typed payload models
# ---------------------------------------------------------------------------


class HealthData(BaseModel):
    """Payload returned by the health-check endpoint."""

    status: str
    version: str
    database: str  # "connected" | "disconnected"


class RootData(BaseModel):
    """Payload returned by the root endpoint."""

    application: str
    status: str
