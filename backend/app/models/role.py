"""
Role ORM model.

A ``Role`` groups users by permission level (e.g. *admin*, *engineer*,
*viewer*).  One role can be assigned to many users.

Table: ``roles``
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    # Imported only for type-checker resolution; avoids circular imports at runtime.
    from app.models.user import User


class Role(UUIDMixin, TimestampMixin, Base):
    """
    Represents an access-control role.

    Relationships:
        * ``users`` — one-to-many with :class:`~app.models.user.User`.
          A single role can be held by many users.
    """

    __tablename__ = "roles"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Short, unique role identifier (e.g. 'admin', 'engineer').",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable explanation of the role's permissions.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: Users that hold this role.
    #: ``lazy="select"`` — load explicitly with ``selectinload`` in queries to
    #: avoid loading all users when only the role itself is needed.
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
        lazy="select",
        doc="All users assigned to this role.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<Role id={self.id!r} name={self.name!r}>"
