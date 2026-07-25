"""
Role-Based Access Control (RBAC) definitions.

Permissions are constants — services and endpoint dependencies check whether
a user's role holds a specific permission before proceeding.

The mapping :data:`ROLE_PERMISSIONS` is the single source of truth for what
each of the four seeded roles can do.  New roles can be added by extending
this dict without touching endpoint code.
"""

from __future__ import annotations

from typing import Final


class Permission:
    """String constants for every permission the system recognises."""

    # Incident permissions
    CREATE_INCIDENT: Final = "incident:create"
    UPDATE_INCIDENT: Final = "incident:update"
    DELETE_INCIDENT: Final = "incident:delete"
    VIEW_INCIDENT: Final = "incident:view"

    # User & role management
    MANAGE_USERS: Final = "users:manage"
    VIEW_USERS: Final = "users:view"
    MANAGE_ROLES: Final = "roles:manage"

    # Documents / RAG
    UPLOAD_DOCUMENT: Final = "document:upload"
    DELETE_DOCUMENT: Final = "document:delete"
    VIEW_DOCUMENT: Final = "document:view"

    # Feedback
    MANAGE_FEEDBACK: Final = "feedback:manage"
    SUBMIT_FEEDBACK: Final = "feedback:submit"

    # System
    MANAGE_SYSTEM: Final = "system:manage"


class Role:
    """Canonical role names (must match the seed data)."""

    ADMIN: Final = "Admin"
    DEVOPS_ENGINEER: Final = "DevOps Engineer"
    AI_ENGINEER: Final = "AI Engineer"
    VIEWER: Final = "Viewer"


# ---------------------------------------------------------------------------
# Role → permission mapping
# ---------------------------------------------------------------------------

#: The single source of truth for RBAC.
#: Extend this dict when adding new roles or permissions.
ROLE_PERMISSIONS: Final[dict[str, frozenset[str]]] = {
    Role.ADMIN: frozenset(
        {
            Permission.CREATE_INCIDENT,
            Permission.UPDATE_INCIDENT,
            Permission.DELETE_INCIDENT,
            Permission.VIEW_INCIDENT,
            Permission.MANAGE_USERS,
            Permission.VIEW_USERS,
            Permission.MANAGE_ROLES,
            Permission.UPLOAD_DOCUMENT,
            Permission.DELETE_DOCUMENT,
            Permission.VIEW_DOCUMENT,
            Permission.MANAGE_FEEDBACK,
            Permission.SUBMIT_FEEDBACK,
            Permission.MANAGE_SYSTEM,
        }
    ),
    Role.DEVOPS_ENGINEER: frozenset(
        {
            Permission.CREATE_INCIDENT,
            Permission.UPDATE_INCIDENT,
            Permission.VIEW_INCIDENT,
            Permission.VIEW_DOCUMENT,
            Permission.SUBMIT_FEEDBACK,
        }
    ),
    Role.AI_ENGINEER: frozenset(
        {
            Permission.VIEW_INCIDENT,
            Permission.UPLOAD_DOCUMENT,
            Permission.DELETE_DOCUMENT,
            Permission.VIEW_DOCUMENT,
            Permission.MANAGE_FEEDBACK,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.VIEW_INCIDENT,
            Permission.VIEW_DOCUMENT,
            Permission.SUBMIT_FEEDBACK,
        }
    ),
}


def has_permission(role_name: str | None, permission: str) -> bool:
    """
    Return ``True`` if *role_name* is granted *permission*.

    Users without an assigned role (``role_name is None``) have no permissions.
    """
    if role_name is None:
        return False
    return permission in ROLE_PERMISSIONS.get(role_name, frozenset())
