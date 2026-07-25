"""
User service.

Business-logic operations for the ``User`` aggregate:

* Create / update / soft-delete users.
* Enforce uniqueness rules (email, username).
* Hash passwords before persistence.
"""

from __future__ import annotations

import uuid

from app.exceptions import DuplicateResourceError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserSelfUpdate, UserUpdate
from app.services.password_service import PasswordService


class UserService:
    """Business-logic layer for user management."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_user(self, payload: UserCreate) -> User:
        """
        Create a new user with a hashed password.

        Raises:
            DuplicateResourceError: When email or username already exists.
        """
        if await self.user_repo.get_by_email(str(payload.email)):
            raise DuplicateResourceError(f"Email '{payload.email}' is already registered.")
        if await self.user_repo.get_by_username(payload.username):
            raise DuplicateResourceError(
                f"Username '{payload.username}' is already taken."
            )

        password_hash = PasswordService.hash(payload.password)
        return await self.user_repo.create(
            id=uuid.uuid4(),
            full_name=payload.full_name,
            username=payload.username.lower(),
            email=str(payload.email).lower(),
            password_hash=password_hash,
            role_id=payload.role_id,
            is_active=True,
            is_verified=False,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Return the user with *user_id*; raise :class:`NotFoundError` otherwise."""
        user = await self.user_repo.get_with_role(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.user_repo.get_by_email(email)

    async def list_users(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str | None,
        sort_order: str,
        search: str | None,
    ) -> tuple[list[User], int]:
        """List active users with pagination and optional search."""
        return await self.user_repo.paginate(
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            search_fields=("username", "email", "full_name"),
            filters={"is_deleted": False},
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> User:
        """Apply an admin-level update to the user with *user_id*."""
        user = await self.get_by_id(user_id)
        updates = payload.model_dump(exclude_unset=True)

        # Enforce email uniqueness if changing.
        if "email" in updates and updates["email"] is not None:
            new_email = str(updates["email"]).lower()
            existing = await self.user_repo.get_by_email(new_email)
            if existing is not None and existing.id != user.id:
                raise DuplicateResourceError(f"Email '{new_email}' is already registered.")
            updates["email"] = new_email

        return await self.user_repo.update(user, **updates)

    async def update_self(self, user: User, payload: UserSelfUpdate) -> User:
        """Apply a self-service update on behalf of the currently authenticated user."""
        updates = payload.model_dump(exclude_unset=True)

        if "email" in updates and updates["email"] is not None:
            new_email = str(updates["email"]).lower()
            existing = await self.user_repo.get_by_email(new_email)
            if existing is not None and existing.id != user.id:
                raise DuplicateResourceError(f"Email '{new_email}' is already registered.")
            updates["email"] = new_email

        return await self.user_repo.update(user, **updates)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def soft_delete_user(self, user_id: uuid.UUID) -> User:
        """Soft-delete the user with *user_id* and deactivate the account."""
        user = await self.get_by_id(user_id)
        user.is_active = False
        return await self.user_repo.soft_delete(user)
