"""
Permission service.

Encapsulates RBAC lookups so endpoint dependencies do not import the raw
mapping directly.
"""

from __future__ import annotations

from app.core.permissions import ROLE_PERMISSIONS, has_permission
from app.models.user import User


class PermissionService:
    """Business logic for role-based access checks."""

    @staticmethod
    def user_permissions(user: User) -> frozenset[str]:
        """Return every permission granted to *user*'s role (empty if roleless)."""
        if user.role is None:
            return frozenset()
        return ROLE_PERMISSIONS.get(user.role.name, frozenset())

    @staticmethod
    def user_has(user: User, permission: str) -> bool:
        """Return ``True`` if *user* has *permission*."""
        role_name = user.role.name if user.role is not None else None
        return has_permission(role_name, permission)

    @staticmethod
    def is_admin(user: User) -> bool:
        """Convenience predicate for admin-only checks."""
        from app.core.permissions import Role

        return user.role is not None and user.role.name == Role.ADMIN
