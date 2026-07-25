"""
Authentication service.

Coordinates the ``User`` and ``TokenService`` to implement the full auth
lifecycle: register, login, refresh, change-password, and logout.
"""

from __future__ import annotations

import uuid

from app.core.logging import get_logger
from app.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.schemas.token import TokenPair
from app.schemas.user import UserCreate
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.services.user_service import UserService

logger = get_logger("services.auth")


class AuthService:
    """High-level orchestration for authentication flows."""

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        role_repo: RoleRepository,
    ) -> None:
        self.user_service = user_service
        self.token_service = token_service
        self.role_repo = role_repo

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, payload: UserCreate, *, default_role: str | None = "Viewer") -> User:
        """
        Register a new user.

        If *default_role* is provided and the user did not supply a ``role_id``,
        the role with that name is looked up and assigned.
        """
        role_obj = None
        if payload.role_id is None and default_role is not None:
            role_obj = await self.role_repo.get_by_name(default_role)
            if role_obj is not None:
                payload.role_id = role_obj.id
        user = await self.user_service.create_user(payload)
        # Attach the role object so the serialised response includes role_name
        # without requiring an extra round-trip through selectinload.
        if role_obj is not None and user.role is None:
            user.role = role_obj
        logger.info("Registered new user: %s (%s)", user.username, user.email)
        return user

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        """
        Authenticate *email* / *password* and issue a token pair.

        Raises:
            InvalidCredentialsError: When credentials do not match.
            InactiveUserError:       When the account exists but is disabled.
        """
        user = await self.user_service.get_by_email(email.lower())
        if user is None or not PasswordService.verify(password, user.password_hash):
            # Constant response regardless of which field is wrong — timing attacks.
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active or user.is_deleted:
            raise InactiveUserError("User account is disabled.")

        # Transparent hash upgrade on successful login.
        if PasswordService.needs_rehash(user.password_hash):
            user.password_hash = PasswordService.hash(password)
            await self.user_service.user_repo.update(user, password_hash=user.password_hash)

        tokens = await self.token_service.issue_pair(user)
        logger.info("User logged in: %s", user.email)
        return user, tokens

    async def logout(self, refresh_token: str) -> None:
        """Revoke *refresh_token* so it can no longer be used."""
        await self.token_service.revoke(refresh_token)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def refresh(self, refresh_token: str) -> tuple[User, TokenPair]:
        """
        Rotate a valid *refresh_token* into a fresh pair.

        Raises:
            InvalidTokenError:   Malformed/expired/revoked.
            InactiveUserError:   User account was disabled after issue.
        """
        record = await self.token_service.verify_refresh_token(refresh_token)
        user = await self.user_service.get_by_id(record.user_id)
        if not user.is_active or user.is_deleted:
            # Nuke every token for the disabled account.
            await self.token_service.revoke_all_for_user(user.id)
            raise InactiveUserError("User account is disabled.")
        tokens = await self.token_service.rotate(user, record)
        return user, tokens

    # ------------------------------------------------------------------
    # Change password
    # ------------------------------------------------------------------

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        """
        Update *user*'s password after verifying *current_password*.

        Revokes every refresh token to force re-login on other devices.
        """
        if not PasswordService.verify(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect.")
        PasswordService.validate_strength(new_password)
        user.password_hash = PasswordService.hash(new_password)
        await self.user_service.user_repo.update(user, password_hash=user.password_hash)
        await self.token_service.revoke_all_for_user(user.id)
        logger.info("Password changed for user %s (%s).", user.username, user.email)
