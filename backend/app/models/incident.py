"""
Incident ORM model.

An ``Incident`` represents a DevOps failure event submitted by an engineer.
The AI pipeline (Milestone 10) analyses incidents and generates remediation
guidance that is stored alongside the incident record.

Table: ``incidents``
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.user import User


class Incident(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a single DevOps incident report.

    Relationships:
        * ``created_by_user`` — many-to-one with :class:`~app.models.user.User`.
        * ``feedbacks``       — one-to-many with :class:`~app.models.feedback.Feedback`.
          Feedbacks are cascade-deleted when the incident is deleted.

    Soft-delete:
        Historical incidents must be retained for AI training; use soft delete
        rather than physical DELETE.

    Indexes:
        * ``status``   — filtered in most listing queries (e.g. "all open").
        * ``severity`` — used to surface critical incidents first.
        * ``created_by`` — supports queries like "incidents by user".
    """

    __tablename__ = "incidents"

    __table_args__ = (
        # Composite index — common query: "open + critical incidents"
        Index(
            "ix_incidents_status_severity",
            "status",
            "severity",
        ),
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Short, descriptive title of the incident.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full description of symptoms and observed behaviour.",
    )
    environment: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Target environment: 'production', 'staging', 'dev', …",
    )
    logs: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Raw log output pasted by the engineer for AI analysis.",
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incidentstatus", create_constraint=True),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
        doc="Current resolution stage of the incident.",
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity, name="incidentseverity", create_constraint=True),
        default=IncidentSeverity.MEDIUM,
        nullable=False,
        index=True,
        doc="Business-impact severity level.",
    )

    # Foreign key — nullable so that deleting a user doesn't cascade-delete incidents.
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_incidents_created_by_users"),
        nullable=True,
        index=True,
        doc="FK → users.id.  The engineer who submitted this incident.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: The user who submitted this incident.
    #: ``lazy="selectin"`` — nearly always displayed next to the incident.
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="incidents",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="User record of the engineer who submitted the incident.",
    )

    #: Feedback entries for this incident.
    #: ``cascade="all, delete-orphan"`` — deleting an incident removes all
    #: associated feedback rows (physical delete is intentional here: feedback
    #: has no standalone value without its parent incident).
    #: ``lazy="select"`` — load explicitly with ``selectinload`` in listings.
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="incident",
        cascade="all, delete-orphan",
        lazy="select",
        doc="User feedback entries associated with this incident.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status_val = self.status.value if self.status is not None else None
        severity_val = self.severity.value if self.severity is not None else None
        return (
            f"<Incident id={self.id!r} title={self.title!r} "
            f"status={status_val!r} severity={severity_val!r}>"
        )
