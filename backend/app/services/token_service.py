"""
Token service.

Owns the full lifecycle of access and refresh tokens:

* Issue a token pair for a user (login, refresh).
* Persist refresh tokens as SHA-256 hashes for revocation.
* Verify and rotate refresh tokens.
* Revoke individual tokens (logout) or every token owned by a user
  (password change, admin action).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from app.config.settings import settings
from app.core.jwt import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.logging import get_logger
from app.exceptions import InvalidTokenError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.token import TokenPair

logger = get_logger("services.token")


def _hash_token(token: str) -> str:
    """SHA-256 hex digest — used to store refresh tokens without the raw value."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenService:
    """Issue, persist, verify, and revoke JWT tokens."""

    def __init__(self, refresh_repo: RefreshTokenRepository) -> None:
        self.refresh_repo = refresh_repo

    # ------------------------------------------------------------------
    # Issue
    # ------------------------------------------------------------------

    async def issue_pair(self, user: User) -> TokenPair:
        """
        Create a new access + refresh token pair for *user*.

        Persists the refresh token hash so it can be revoked.
        """
        extra: dict[str, str] = {}
        # role attribute is loaded via selectinload in UserRepository.get_with_role.
        if user.role is not None:
            extra["role"] = user.role.name

        access = create_access_token(subject=str(user.id), extra_claims=extra)
        refresh = create_refresh_token(subject=str(user.id))

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_repo.create(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=_hash_token(refresh),
            expires_at=expires_at,
        )

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Verify / decode
    # ------------------------------------------------------------------

    def decode_access_token(self, token: str) -> dict:
        """Decode *token* and ensure it is an access token."""
        try:
            return decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
        except JWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

    async def verify_refresh_token(self, token: str) -> RefreshToken:
        """
        Verify a refresh *token* is signed, unexpired, non-revoked, and stored.

        Returns the matching :class:`RefreshToken` record.

        Raises:
            InvalidTokenError: On any failure.
        """
        try:
            decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
        except JWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        record = await self.refresh_repo.get_by_hash(_hash_token(token))
        if record is None:
            raise InvalidTokenError("Refresh token is not recognised.")
        if record.revoked_at is not None:
            raise InvalidTokenError("Refresh token has been revoked.")
        # Compare expiry in UTC.
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise InvalidTokenError("Refresh token has expired.")
        return record

    # ------------------------------------------------------------------
    # Rotate / revoke
    # ------------------------------------------------------------------

    async def rotate(self, user: User, old_token: RefreshToken) -> TokenPair:
        """Revoke *old_token* and issue a fresh pair for *user*."""
        await self.refresh_repo.revoke(old_token)
        return await self.issue_pair(user)

    async def revoke(self, token: str) -> None:
        """Revoke a single refresh token identified by its raw value."""
        record = await self.refresh_repo.get_by_hash(_hash_token(token))
        if record is not None and record.revoked_at is None:
            await self.refresh_repo.revoke(record)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke every active refresh token for *user_id*."""
        count = await self.refresh_repo.revoke_all_for_user(user_id)
        logger.info("Revoked %d refresh token(s) for user %s.", count, user_id)
        return count
