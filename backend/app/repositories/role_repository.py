"""Role repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Data-access operations for the :class:`~app.models.role.Role` model."""

    model = Role

    async def get_by_name(self, name: str) -> Role | None:
        """Return the role with the given *name*, or ``None``."""
        stmt = select(Role).where(Role.name == name).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()
