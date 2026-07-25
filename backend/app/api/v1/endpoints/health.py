"""
Health check endpoint.

Route: GET /api/v1/health
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import settings
from app.schemas.response import HealthData, StandardResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=StandardResponse[HealthData],
    summary="Health check",
    description="Returns the current health status and version of the service.",
    tags=["Health"],
)
async def health_check() -> StandardResponse[HealthData]:
    """
    Confirm the API is alive and return its version string.

    Returns:
        ``StandardResponse`` with a ``HealthData`` payload.
    """
    return StandardResponse(
        success=True,
        message="Service is healthy.",
        data=HealthData(status="healthy", version=settings.APP_VERSION),
    )
