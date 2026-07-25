"""
SQLAlchemy declarative base with a consistent constraint naming convention.

All ORM model classes must inherit from ``Base``.  Alembic's ``env.py``
imports ``Base.metadata`` to auto-detect schema changes for migrations.

The ``NAMING_CONVENTION`` ensures every constraint and index receives a
predictable, deterministic name — critical for repeatable Alembic migrations
across environments.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Naming convention
# Alembic requires explicit names on all constraints to generate reliable
# ``ALTER TABLE`` DDL.  These patterns produce names like:
#   ix_users_email, uq_users_email, fk_incidents_created_by_users, …
# ---------------------------------------------------------------------------
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Shared declarative base for all application ORM models.

    All models inheriting from ``Base`` will have their tables registered
    with the shared ``MetaData`` object, making them visible to Alembic's
    ``--autogenerate`` command.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

