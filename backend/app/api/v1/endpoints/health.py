"""
Health check endpoint.

Route: GET /api/v1/health

Returns the service health status and database connectivity.
When the database is unreachable the HTTP status is still 200 but the
response body reflects a degraded state so upstream load balancers can
distinguish application errors from infrastructure failures.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import settings
from app.database.database import db_manager
from app.schemas.response import HealthData, StandardResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=StandardResponse[HealthData],
    summary="Health check",
    description=(
        "Returns the current health status, database connectivity, "
        "and version of the service."
    ),
    tags=["Health"],
)
async def health_check() -> StandardResponse[HealthData]:
    """
    Confirm the API is alive, verify database connectivity, and return version.

    Returns:
        ``StandardResponse`` with a ``HealthData`` payload.
        ``status`` is ``"healthy"`` when the database is reachable,
        ``"degraded"`` when it is not.
    """
    db_ok = await db_manager.ping()

    if db_ok:
        return StandardResponse(
            success=True,
            message="Service is healthy.",
            data=HealthData(
                status="healthy",
                database="connected",
                version=settings.APP_VERSION,
            ),
        )

    return StandardResponse(
        success=True,
        message="Service is degraded: database unreachable.",
        data=HealthData(
            status="degraded",
            database="disconnected",
            version=settings.APP_VERSION,
        ),
    )
