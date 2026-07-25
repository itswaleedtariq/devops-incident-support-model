"""Tests for the RBAC permission system."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.core.permissions import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    has_permission,
)
from app.services.permission_service import PermissionService


class TestRolePermissionsMap:
    def test_all_four_roles_present(self) -> None:
        names = {Role.ADMIN, Role.DEVOPS_ENGINEER, Role.AI_ENGINEER, Role.VIEWER}
        assert names.issubset(ROLE_PERMISSIONS.keys())

    def test_admin_has_manage_users(self) -> None:
        assert Permission.MANAGE_USERS in ROLE_PERMISSIONS[Role.ADMIN]

    def test_admin_has_all_permissions(self) -> None:
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        # Admin should hold every permission any other role holds.
        for other, perms in ROLE_PERMISSIONS.items():
            if other == Role.ADMIN:
                continue
            assert perms.issubset(admin_perms), (
                f"Admin missing permissions granted to {other}: {perms - admin_perms}"
            )

    def test_viewer_cannot_manage_users(self) -> None:
        assert Permission.MANAGE_USERS not in ROLE_PERMISSIONS[Role.VIEWER]

    def test_devops_engineer_cannot_delete_document(self) -> None:
        assert Permission.DELETE_DOCUMENT not in ROLE_PERMISSIONS[Role.DEVOPS_ENGINEER]

    def test_ai_engineer_can_upload_document(self) -> None:
        assert Permission.UPLOAD_DOCUMENT in ROLE_PERMISSIONS[Role.AI_ENGINEER]


class TestHasPermission:
    def test_none_role_has_no_permissions(self) -> None:
        assert has_permission(None, Permission.VIEW_INCIDENT) is False

    def test_unknown_role_has_no_permissions(self) -> None:
        assert has_permission("Unknown", Permission.VIEW_INCIDENT) is False

    def test_admin_has_manage_system(self) -> None:
        assert has_permission(Role.ADMIN, Permission.MANAGE_SYSTEM) is True


class TestPermissionService:
    def _mock_user(self, role_name: str | None) -> MagicMock:
        user = MagicMock()
        if role_name is None:
            user.role = None
        else:
            user.role = MagicMock()
            user.role.name = role_name
        return user

    def test_user_permissions_admin(self) -> None:
        user = self._mock_user(Role.ADMIN)
        assert PermissionService.user_permissions(user) == ROLE_PERMISSIONS[Role.ADMIN]

    def test_user_permissions_no_role(self) -> None:
        assert PermissionService.user_permissions(self._mock_user(None)) == frozenset()

    def test_user_has_permission(self) -> None:
        user = self._mock_user(Role.VIEWER)
        assert PermissionService.user_has(user, Permission.VIEW_INCIDENT) is True
        assert PermissionService.user_has(user, Permission.MANAGE_USERS) is False

    def test_is_admin(self) -> None:
        assert PermissionService.is_admin(self._mock_user(Role.ADMIN)) is True
        assert PermissionService.is_admin(self._mock_user(Role.VIEWER)) is False
        assert PermissionService.is_admin(self._mock_user(None)) is False
