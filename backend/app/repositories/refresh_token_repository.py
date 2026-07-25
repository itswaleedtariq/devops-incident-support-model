"""Refresh-token repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Data-access operations for :class:`~app.models.refresh_token.RefreshToken`."""

    model = RefreshToken

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return the refresh-token record by its SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        """Mark *token* as revoked."""
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        await self.session.flush()
        return token

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """
        Revoke every active refresh token for *user_id*.

        Returns the number of tokens revoked.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)
