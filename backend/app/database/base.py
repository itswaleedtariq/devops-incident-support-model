"""
SQLAlchemy declarative base.

All ORM model classes must inherit from ``Base``.  Alembic's ``env.py``
imports ``Base.metadata`` to auto-detect schema changes for migrations.

Example (Milestone 2.2)::

    from app.database.base import Base

    class Incident(Base):
        __tablename__ = "incidents"
        id: Mapped[int] = mapped_column(primary_key=True)
        ...
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared declarative base for all application ORM models.

    Import this class in every model module to register the model with
    SQLAlchemy's metadata, which Alembic uses for migration generation.
    """
