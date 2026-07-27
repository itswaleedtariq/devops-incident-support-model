"""
Authentication dependencies.

* ``get_current_user`` — decode the Bearer token and load the User.
* ``get_current_active_user`` — additionally require the account is active.
* ``get_current_admin`` — additionally require the Admin role.
* ``require_permission("permission:name")`` — factory for permission checks.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Coroutine

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.permissions import Role
from app.dependencies.services import get_token_service, get_user_service
from app.exceptions import InvalidTokenError
from app.models.user import User
from app.services.permission_service import PermissionService

# Reusable HTTP Bearer scheme — surfaces in Swagger UI as a lock icon.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    token_service: Any = Depends(get_token_service),
    user_service: Any = Depends(get_user_service),
) -> User:
    """
    Decode the Bearer access token and return the authenticated user.

    Raises:
        HTTPException(401): On missing / malformed / expired token.
        HTTPException(404): On token referencing a non-existent user.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = token_service.decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is missing or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        return await user_service.get_by_id(user_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject does not correspond to a known user.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject does not correspond to a known user.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Require an active, non-deleted user."""
    if not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return user


async def get_current_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Require the current user to hold the ``Admin`` role."""
    if user.role is None or user.role.name != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return user


def require_permission(
    permission: str,
) -> Callable[[User], Coroutine[None, None, User]]:
    """
    Factory returning a dependency that enforces a specific permission.

    Usage::

        @router.delete("/documents/{doc_id}")
        async def delete_doc(
            _: User = Depends(require_permission(Permission.DELETE_DOCUMENT)),
        ): ...
    """

    async def _dependency(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if not PermissionService.user_has(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return user

    return _dependency
