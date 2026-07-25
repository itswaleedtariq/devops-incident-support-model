"""
RefreshToken ORM model.

Refresh tokens are stored server-side so they can be revoked (logout,
password change, admin action) without waiting for the token to expire.

Only the SHA-256 hash of the token is stored — the raw token is never
persisted, following the same principle as password hashing.

Table: ``refresh_tokens``
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(UUIDMixin, Base):
    """
    Represents an issued refresh token.

    Only the SHA-256 hash of the token is stored (``token_hash``).  The
    plain token is returned to the client at issue-time and never persisted.

    A token is *usable* iff:
        * ``revoked_at IS NULL``
        * ``expires_at > now()``
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            name="fk_refresh_tokens_user_id_users",
        ),
        nullable=False,
        index=True,
        doc="FK → users.id.  Cascade-deletes when the user is removed.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hex digest of the raw refresh token.  Never store the raw token.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC expiry timestamp; tokens are rejected after this instant.",
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC revocation timestamp; ``NULL`` when the token is still active.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp of issue.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: The user this token authenticates.  ``lazy="selectin"`` because auth
    #: middleware always needs the user identity together with the token.
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        doc="User that owns this refresh token.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id!r} user_id={self.user_id!r} "
            f"revoked={self.revoked_at is not None!r}>"
        )
