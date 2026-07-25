"""
User management endpoints.

Routes:
    GET    /api/v1/users            List users (admin only).
    GET    /api/v1/users/me         Self.
    PATCH  /api/v1/users/me         Update self.
    GET    /api/v1/users/{id}       Get user by ID (admin only).
    PATCH  /api/v1/users/{id}       Update user (admin only).
    DELETE /api/v1/users/{id}       Soft-delete user (admin only).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.current_user import get_current_active_user, get_current_admin
from app.dependencies.services import get_user_service
from app.exceptions import DuplicateResourceError, NotFoundError
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.response import StandardResponse
from app.schemas.user import UserRead, UserSelfUpdate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

_SORTABLE_COLUMNS = {"username", "email", "created_at", "updated_at", "full_name"}


def _to_user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role_id=user.role_id,
        role_name=user.role.name if user.role is not None else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /users/me   (put BEFORE /{user_id} — order matters in FastAPI)
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=StandardResponse[UserRead],
    summary="Return the authenticated user's profile",
)
async def read_me(
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse[UserRead]:
    return StandardResponse(success=True, message="OK.", data=_to_user_read(current_user))


@router.patch(
    "/me",
    response_model=StandardResponse[UserRead],
    summary="Update the authenticated user's profile",
)
async def update_me(
    payload: UserSelfUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> StandardResponse[UserRead]:
    try:
        user = await user_service.update_self(current_user, payload)
    except DuplicateResourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return StandardResponse(
        success=True, message="Profile updated.", data=_to_user_read(user)
    )


# ---------------------------------------------------------------------------
# GET /users  (admin)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=StandardResponse[PaginatedResponse[UserRead]],
    summary="List users (admin only)",
    dependencies=[Depends(get_current_admin)],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: str | None = Query(None, max_length=200),
    user_service: UserService = Depends(get_user_service),
) -> StandardResponse[PaginatedResponse[UserRead]]:
    """Return a paginated list of users.  Admin only."""
    if sort_by is not None and sort_by not in _SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot sort by '{sort_by}'.",
        )
    offset = (page - 1) * page_size
    users, total = await user_service.list_users(
        offset=offset,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    payload = PaginatedResponse[UserRead](
        items=[_to_user_read(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return StandardResponse(success=True, message="OK.", data=payload)


# ---------------------------------------------------------------------------
# GET / PATCH / DELETE  /users/{user_id}  (admin)
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserRead],
    summary="Get a user by ID (admin only)",
    dependencies=[Depends(get_current_admin)],
)
async def get_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
) -> StandardResponse[UserRead]:
    try:
        user = await user_service.get_by_id(user_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return StandardResponse(success=True, message="OK.", data=_to_user_read(user))


@router.patch(
    "/{user_id}",
    response_model=StandardResponse[UserRead],
    summary="Update a user (admin only)",
    dependencies=[Depends(get_current_admin)],
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    user_service: UserService = Depends(get_user_service),
) -> StandardResponse[UserRead]:
    try:
        user = await user_service.update_user(user_id, payload)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DuplicateResourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return StandardResponse(success=True, message="User updated.", data=_to_user_read(user))


@router.delete(
    "/{user_id}",
    response_model=StandardResponse[None],
    summary="Soft-delete a user (admin only)",
    dependencies=[Depends(get_current_admin)],
)
async def delete_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
) -> StandardResponse[None]:
    try:
        await user_service.soft_delete_user(user_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return StandardResponse(success=True, message="User deleted.", data=None)
