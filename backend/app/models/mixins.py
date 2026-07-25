"""
Reusable SQLAlchemy 2.x declarative mixins.

Mixins add common column groups to any ORM model without duplicating column
definitions.  They are plain Python classes — they do **not** inherit from
``Base`` — and are mixed in via Python's multiple-inheritance mechanism.

Usage::

    from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

    class Incident(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
        __tablename__ = "incidents"
        ...

Column ordering in the resulting table follows Python's MRO:
    1. Model's own columns  (defined in the model class)
    2. UUIDMixin.id
    3. TimestampMixin.created_at / updated_at
    4. SoftDeleteMixin.is_deleted / deleted_at
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """
    Provides a ``uuid.UUID`` primary key column named ``id``.

    The UUID is generated at the Python level (``uuid.uuid4``) so the value
    is available on the object immediately after instantiation — before the
    INSERT round-trip to the database.  This enables passing the ID to
    downstream systems (message queues, caches) without an extra DB query.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Globally unique primary key (UUID v4).",
    )


class TimestampMixin:
    """
    Provides ``created_at`` and ``updated_at`` timestamp columns.

    * ``created_at`` — set once at INSERT by the database (``server_default``).
    * ``updated_at`` — set at INSERT and refreshed on every UPDATE at the
      SQLAlchemy ORM level (``onupdate``).

    Both columns store timezone-aware timestamps (``TIMESTAMP WITH TIME ZONE``
    in PostgreSQL) to avoid UTC/local-time ambiguity in multi-region deploys.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp — set automatically on row creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp — updated automatically on every modification.",
    )


class SoftDeleteMixin:
    """
    Provides soft-delete support via ``is_deleted`` and ``deleted_at`` columns.

    Soft deletion preserves historical data (important for audit logs and AI
    training) while hiding records from normal application queries.

    Convention: every query in the repository layer must filter on
    ``is_deleted == False`` unless explicitly retrieving deleted records.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
        doc="``True`` when the record has been soft-deleted.",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of soft deletion; ``NULL`` when not deleted.",
    )
