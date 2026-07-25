"""
Feedback ORM model.

A ``Feedback`` record captures an engineer's rating and comment on a
specific incident's AI-generated remediation guidance.  Feedback drives
the model evaluation pipeline (Milestone 5).

Table: ``feedbacks``

Note:
    Feedback is intentionally immutable — there is no ``updated_at`` column.
    Engineers submit a single rating per incident; mutation would skew RLHF
    signal quality.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class Feedback(UUIDMixin, Base):
    """
    Represents user feedback on an incident's AI-generated response.

    Relationships:
        * ``incident`` — many-to-one with :class:`~app.models.incident.Incident`.
        * ``user``     — many-to-one with :class:`~app.models.user.User`.

    Constraints:
        * ``rating`` must be between 1 (poor) and 5 (excellent).
        * A ``CHECK`` constraint enforces this at the database level for
          data integrity independent of application-layer validation.

    Cascade:
        Feedback rows are physically deleted when the parent incident is
        deleted (``cascade="all, delete-orphan"`` on ``Incident.feedbacks``).
        The ``ON DELETE CASCADE`` on the FK provides a DB-level safety net.
    """

    __tablename__ = "feedbacks"

    __table_args__ = (
        # Enforce rating range at DB level — application validation is not enough.
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_feedbacks_rating_range",
        ),
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "incidents.id",
            ondelete="CASCADE",
            name="fk_feedbacks_incident_id_incidents",
        ),
        nullable=False,
        index=True,
        doc="FK → incidents.id.  Cascades on physical incident delete.",
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            name="fk_feedbacks_user_id_users",
        ),
        nullable=True,
        index=True,
        doc="FK → users.id.  Set to NULL when the user is deleted.",
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Quality rating from 1 (poor) to 5 (excellent).",
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional free-text explanation of the rating.",
    )
    # Feedback has only created_at (no updated_at — feedback is immutable).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp — set automatically on row creation.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: The incident this feedback refers to.
    #: ``lazy="selectin"`` — always displayed alongside the feedback entry.
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="feedbacks",
        lazy="selectin",
        doc="Parent incident for this feedback.",
    )

    #: The user who submitted the feedback.
    #: ``lazy="selectin"`` — author info is always displayed with feedback.
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="feedbacks",
        foreign_keys=[user_id],
        lazy="selectin",
        doc="User who authored this feedback entry.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Feedback id={self.id!r} incident_id={self.incident_id!r} "
            f"rating={self.rating!r}>"
        )
