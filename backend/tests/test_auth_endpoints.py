"""
End-to-end tests for authentication and user endpoints.

These tests exercise the full FastAPI stack (routers, dependencies,
services, schemas) with the database and repositories replaced by
in-memory fakes.  No PostgreSQL is required.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.permissions import Role as RoleName
from app.dependencies.repositories import (
    get_refresh_token_repository,
    get_role_repository,
    get_user_repository,
)
from app.main import create_app
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.services.password_service import PasswordService


# ---------------------------------------------------------------------------
# In-memory fake repositories
# ---------------------------------------------------------------------------


class FakeUserRepo:
    """Minimal in-memory replacement for :class:`UserRepository`."""

    def __init__(self) -> None:
        self._users: dict[uuid.UUID, User] = {}

    # BaseRepository-like API used by the services under test -----------

    async def create(self, **fields: Any) -> User:
        user = User(**fields)
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.is_deleted = False
        user.deleted_at = None
        self._users[user.id] = user
        return user

    async def update(self, instance: User, **fields: Any) -> User:
        for k, v in fields.items():
            setattr(instance, k, v)
        instance.updated_at = datetime.now(timezone.utc)
        self._users[instance.id] = instance
        return instance

    async def soft_delete(self, instance: User) -> User:
        instance.is_deleted = True
        instance.deleted_at = datetime.now(timezone.utc)
        self._users[instance.id] = instance
        return instance

    async def paginate(self, *, offset, limit, sort_by, sort_order, search, search_fields, filters):
        items = [
            u for u in self._users.values()
            if not (filters.get("is_deleted") and u.is_deleted)
        ]
        if search:
            s = search.lower()
            items = [
                u for u in items
                if s in (u.username or "").lower()
                or s in (u.email or "").lower()
                or s in (u.full_name or "").lower()
            ]
        total = len(items)
        return items[offset:offset + limit], total

    # UserRepository-specific helpers -----------------------------------

    async def get_by_email(self, email: str) -> User | None:
        for u in self._users.values():
            if u.email == email.lower():
                return u
        return None

    async def get_by_username(self, username: str) -> User | None:
        for u in self._users.values():
            if u.username == username.lower():
                return u
        return None

    async def get_with_role(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)


class FakeRoleRepo:
    def __init__(self) -> None:
        self._roles_by_name: dict[str, Role] = {}
        for name in (RoleName.ADMIN, RoleName.DEVOPS_ENGINEER, RoleName.AI_ENGINEER, RoleName.VIEWER):
            r = Role(name=name, description=f"{name} role")
            r.id = uuid.uuid4()
            r.created_at = datetime.now(timezone.utc)
            r.updated_at = datetime.now(timezone.utc)
            self._roles_by_name[name] = r

    async def get_by_name(self, name: str) -> Role | None:
        return self._roles_by_name.get(name)

    def get(self, name: str) -> Role:
        return self._roles_by_name[name]


class FakeRefreshRepo:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, RefreshToken] = {}
        self._by_hash: dict[str, RefreshToken] = {}

    async def create(self, **fields: Any) -> RefreshToken:
        rt = RefreshToken(**fields)
        rt.created_at = datetime.now(timezone.utc)
        rt.revoked_at = None
        self._by_id[rt.id] = rt
        self._by_hash[rt.token_hash] = rt
        return rt

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self._by_hash.get(token_hash)

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        token.revoked_at = datetime.now(timezone.utc)
        return token

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        count = 0
        for rt in self._by_id.values():
            if rt.user_id == user_id and rt.revoked_at is None:
                rt.revoked_at = datetime.now(timezone.utc)
                count += 1
        return count


# ---------------------------------------------------------------------------
# App + fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_stack():
    """Return (app, user_repo, role_repo, refresh_repo) with overrides installed."""
    app = create_app()
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    user_repo = FakeUserRepo()
    role_repo = FakeRoleRepo()
    refresh_repo = FakeRefreshRepo()

    # Pre-assign every user a role so JWT claims include role_name.
    # (Handled by the service — Viewer is default.)

    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_role_repository] = lambda: role_repo
    app.dependency_overrides[get_refresh_token_repository] = lambda: refresh_repo

    return app, user_repo, role_repo, refresh_repo


@pytest.fixture
def api(fake_stack) -> TestClient:
    """A TestClient wrapping the overridden app."""
    app, *_ = fake_stack
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


# ---------------------------------------------------------------------------
# Helper — a valid registration payload
# ---------------------------------------------------------------------------

VALID_USER = {
    "full_name": "Test User",
    "username": "testuser",
    "email": "test@example.com",
    "password": "StrongPass1!",
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_success(self, api: TestClient) -> None:
        r = api.post("/api/v1/auth/register", json=VALID_USER)
        assert r.status_code == status.HTTP_201_CREATED, r.text
        body = r.json()
        assert body["success"] is True
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["role_name"] == RoleName.VIEWER

    def test_register_duplicate_email(self, api: TestClient) -> None:
        api.post("/api/v1/auth/register", json=VALID_USER)
        r = api.post("/api/v1/auth/register", json=VALID_USER)
        assert r.status_code == status.HTTP_409_CONFLICT

    def test_register_weak_password_rejected(self, api: TestClient) -> None:
        payload = {**VALID_USER, "password": "weak"}
        r = api.post("/api/v1/auth/register", json=payload)
        assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_email(self, api: TestClient) -> None:
        payload = {**VALID_USER, "email": "not-an-email"}
        r = api.post("/api/v1/auth/register", json=payload)
        assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Login / Me / Logout / Refresh
# ---------------------------------------------------------------------------


class TestLoginFlow:
    def _register(self, api: TestClient, payload: dict | None = None) -> None:
        api.post("/api/v1/auth/register", json=payload or VALID_USER)

    def test_login_success(self, api: TestClient) -> None:
        self._register(api)
        r = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, api: TestClient) -> None:
        self._register(api)
        r = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": "WrongPass1!"},
        )
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api: TestClient) -> None:
        r = api.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "SomePass1!"},
        )
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_current_user(self, api: TestClient) -> None:
        self._register(api)
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        access = login.json()["data"]["access_token"]
        r = api.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["email"] == VALID_USER["email"]

    def test_me_without_token(self, api: TestClient) -> None:
        r = api.get("/api/v1/auth/me")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_invalid_token(self, api: TestClient) -> None:
        r = api.get("/api/v1/auth/me", headers={"Authorization": "Bearer nope.nope.nope"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_rotates_tokens(self, api: TestClient) -> None:
        self._register(api)
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        refresh1 = login.json()["data"]["refresh_token"]
        r = api.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
        assert r.status_code == 200, r.text
        refresh2 = r.json()["data"]["refresh_token"]
        assert refresh2 != refresh1

        # Old refresh should now be revoked.
        r_again = api.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
        assert r_again.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_revokes_token(self, api: TestClient) -> None:
        self._register(api)
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        refresh = login.json()["data"]["refresh_token"]
        r = api.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        assert r.status_code == 200
        # After logout the refresh token must not be usable.
        r2 = api.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r2.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------


class TestChangePassword:
    def _login(self, api: TestClient) -> str:
        api.post("/api/v1/auth/register", json=VALID_USER)
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        return login.json()["data"]["access_token"]

    def test_change_password_success(self, api: TestClient) -> None:
        access = self._login(api)
        r = api.post(
            "/api/v1/auth/change-password",
            json={"current_password": VALID_USER["password"], "new_password": "NewStrong1!"},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == 200
        # Login with new password now works.
        r2 = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": "NewStrong1!"},
        )
        assert r2.status_code == 200

    def test_change_password_wrong_current(self, api: TestClient) -> None:
        access = self._login(api)
        r = api.post(
            "/api/v1/auth/change-password",
            json={"current_password": "Wrong1!Pass", "new_password": "NewStrong1!"},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# RBAC on user endpoints
# ---------------------------------------------------------------------------


class TestRBACOnUserEndpoints:
    """Non-admins must be blocked from admin-only endpoints."""

    def _viewer_access(self, api: TestClient) -> str:
        api.post("/api/v1/auth/register", json=VALID_USER)  # gets Viewer role
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        return login.json()["data"]["access_token"]

    def test_viewer_cannot_list_users(self, api: TestClient) -> None:
        access = self._viewer_access(api)
        r = api.get("/api/v1/users", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_cannot_delete_user(self, api: TestClient) -> None:
        access = self._viewer_access(api)
        r = api.delete(
            f"/api/v1/users/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_can_read_own_profile(self, api: TestClient) -> None:
        access = self._viewer_access(api)
        r = api.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200

    def test_users_list_requires_auth(self, api: TestClient) -> None:
        r = api.get("/api/v1/users")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Admin flows
# ---------------------------------------------------------------------------


class TestAdminEndpoints:
    def _admin_access(self, api: TestClient, fake_stack) -> tuple[str, uuid.UUID]:
        """Register a user, mutate their role to Admin, and log in."""
        _, user_repo, role_repo, _ = fake_stack
        api.post("/api/v1/auth/register", json=VALID_USER)
        # Promote to Admin
        admin_role = role_repo.get(RoleName.ADMIN)
        user = list(user_repo._users.values())[0]
        user.role = admin_role
        user.role_id = admin_role.id
        login = api.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        return login.json()["data"]["access_token"], user.id

    def test_admin_can_list_users(self, api: TestClient, fake_stack) -> None:
        access, _ = self._admin_access(api, fake_stack)
        r = api.get("/api/v1/users", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

    def test_admin_can_get_user_by_id(self, api: TestClient, fake_stack) -> None:
        access, user_id = self._admin_access(api, fake_stack)
        r = api.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == 200

    def test_admin_can_delete_user(self, api: TestClient, fake_stack) -> None:
        access, user_id = self._admin_access(api, fake_stack)
        r = api.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert r.status_code == 200
