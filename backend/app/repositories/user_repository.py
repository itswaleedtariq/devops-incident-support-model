"""User repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data-access operations for the :class:`~app.models.user.User` model."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given *email*, or ``None``."""
        stmt = (
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.role))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Return the user with the given *username*, or ``None``."""
        stmt = (
            select(User)
            .where(User.username == username.lower())
            .options(selectinload(User.role))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_with_role(self, user_id: uuid.UUID) -> User | None:
        """Return the user with its role eagerly loaded, or ``None``."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
