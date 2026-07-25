"""
User ORM model.

A ``User`` represents an authenticated engineer or administrator who can
submit incidents and provide feedback.

Table: ``users``
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.incident import Incident
    from app.models.role import Role


class User(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents an application user (engineer, admin, or viewer).

    Relationships:
        * ``role``      — many-to-one with :class:`~app.models.role.Role`.
        * ``incidents`` — one-to-many with :class:`~app.models.incident.Incident`.
        * ``feedbacks`` — one-to-many with :class:`~app.models.feedback.Feedback`.

    Soft-delete:
        Records are *never physically deleted* so that audit trails and
        AI training data referencing the user remain intact.
        Set ``is_deleted = True`` and ``deleted_at = <now>`` to deactivate.
    """

    __tablename__ = "users"

    __table_args__ = (
        # Explicit unique constraint names for reliable Alembic DDL generation.
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Display name shown in the UI.",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Unique login handle (URL-safe, lowercase).",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Primary contact address; must be globally unique.",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2 / bcrypt hash of the user's password. Never store plaintext.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="``False`` disables login without deleting the account.",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="``True`` once the email address has been confirmed.",
    )

    # Foreign key — nullable so that deleting a Role does not cascade-delete users.
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL", name="fk_users_role_id_roles"),
        nullable=True,
        index=True,
        doc="FK → roles.id.  ``NULL`` when no role is assigned.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: The role assigned to this user.
    #: ``lazy="selectin"`` — a user's role is almost always needed together
    #: with the user object, so we batch-load it in a single extra SELECT.
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin",
        doc="The access-control role assigned to this user.",
    )

    #: Incidents created by this user.
    #: ``lazy="select"`` — a user may have many thousands of incidents;
    #: use ``selectinload(User.incidents)`` explicitly in listing queries.
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="created_by_user",
        foreign_keys="[Incident.created_by]",
        lazy="select",
        doc="All incidents submitted by this user.",
    )

    #: Feedback entries submitted by this user.
    #: ``lazy="select"`` — load explicitly when needed.
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="user",
        foreign_keys="[Feedback.user_id]",
        lazy="select",
        doc="All feedback entries authored by this user.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<User id={self.id!r} username={self.username!r} "
            f"email={self.email!r} active={self.is_active!r}>"
        )
