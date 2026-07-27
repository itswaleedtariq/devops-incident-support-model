"""Incident management API.

Routes:
    POST   /api/v1/incidents
    GET    /api/v1/incidents
    GET    /api/v1/incidents/history
    GET    /api/v1/incidents/{incident_id}
    PATCH  /api/v1/incidents/{incident_id}
    PATCH  /api/v1/incidents/{incident_id}/status
    DELETE /api/v1/incidents/{incident_id}
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status

from app.core.permissions import Permission
from app.dependencies.current_user import require_permission
from app.dependencies.services import get_incident_service
from app.exceptions import DomainValidationError, NotFoundError
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.incident import (
    IncidentCreate,
    IncidentRead,
    IncidentStatusUpdate,
    IncidentUpdate,
)
from app.schemas.response import StandardResponse
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidents"])

_SORTABLE_COLUMNS = {
    "created_at",
    "updated_at",
    "title",
    "status",
    "severity",
    "environment",
}


def _to_read(incident: Incident) -> IncidentRead:
    return IncidentRead.model_validate(incident)


async def _list_payload(
    *,
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    search: str | None,
    incident_status: IncidentStatus | None,
    severity: IncidentSeverity | None,
    environment: str | None,
    current_user: User,
    service: IncidentService,
) -> StandardResponse[PaginatedResponse[IncidentRead]]:
    if sort_by not in _SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot sort incidents by '{sort_by}'.",
        )
    items, total = await service.list_incidents(
        user=current_user,
        offset=(page - 1) * page_size,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        status=incident_status,
        severity=severity,
        environment=environment,
    )
    pages = (total + page_size - 1) // page_size
    return StandardResponse(
        success=True,
        message="Incident history retrieved.",
        data=PaginatedResponse[IncidentRead](
            items=[_to_read(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.post(
    "",
    response_model=StandardResponse[IncidentRead],
    status_code=http_status.HTTP_201_CREATED,
    summary="Create an incident",
)
async def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[IncidentRead]:
    incident = await service.create_incident(payload, current_user)
    return StandardResponse(
        success=True,
        message="Incident created.",
        data=_to_read(incident),
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedResponse[IncidentRead]],
    summary="List and search incidents",
)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: str | None = Query(None, max_length=200),
    incident_status: IncidentStatus | None = Query(None, alias="status"),
    severity: IncidentSeverity | None = Query(None),
    environment: str | None = Query(None, max_length=100),
    current_user: User = Depends(require_permission(Permission.VIEW_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[PaginatedResponse[IncidentRead]]:
    return await _list_payload(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        incident_status=incident_status,
        severity=severity,
        environment=environment,
        current_user=current_user,
        service=service,
    )


@router.get(
    "/history",
    response_model=StandardResponse[PaginatedResponse[IncidentRead]],
    summary="Return incident history",
)
async def incident_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: str | None = Query(None, max_length=200),
    incident_status: IncidentStatus | None = Query(None, alias="status"),
    severity: IncidentSeverity | None = Query(None),
    environment: str | None = Query(None, max_length=100),
    current_user: User = Depends(require_permission(Permission.VIEW_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[PaginatedResponse[IncidentRead]]:
    return await _list_payload(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        incident_status=incident_status,
        severity=severity,
        environment=environment,
        current_user=current_user,
        service=service,
    )


@router.get(
    "/{incident_id}",
    response_model=StandardResponse[IncidentRead],
    summary="Get an incident",
)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.VIEW_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[IncidentRead]:
    try:
        incident = await service.get_incident(incident_id, current_user)
    except NotFoundError as exc:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StandardResponse(success=True, message="OK.", data=_to_read(incident))


@router.patch(
    "/{incident_id}",
    response_model=StandardResponse[IncidentRead],
    summary="Update an incident",
)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    current_user: User = Depends(require_permission(Permission.UPDATE_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[IncidentRead]:
    try:
        incident = await service.update_incident(incident_id, payload, current_user)
    except NotFoundError as exc:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomainValidationError as exc:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return StandardResponse(
        success=True,
        message="Incident updated.",
        data=_to_read(incident),
    )


@router.patch(
    "/{incident_id}/status",
    response_model=StandardResponse[IncidentRead],
    summary="Update incident status",
)
async def update_incident_status(
    incident_id: uuid.UUID,
    payload: IncidentStatusUpdate,
    current_user: User = Depends(require_permission(Permission.UPDATE_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[IncidentRead]:
    try:
        incident = await service.update_status(incident_id, payload, current_user)
    except NotFoundError as exc:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StandardResponse(
        success=True,
        message="Incident status updated.",
        data=_to_read(incident),
    )


@router.delete(
    "/{incident_id}",
    response_model=StandardResponse[None],
    summary="Soft-delete an incident",
)
async def delete_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.DELETE_INCIDENT)),
    service: IncidentService = Depends(get_incident_service),
) -> StandardResponse[None]:
    try:
        await service.delete_incident(incident_id, current_user)
    except NotFoundError as exc:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StandardResponse(success=True, message="Incident deleted.", data=None)
