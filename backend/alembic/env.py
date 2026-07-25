"""
Alembic migration environment.

This module is executed by every ``alembic`` CLI command.  It:

1. Loads application settings to obtain the database URL.
2. Imports ``Base.metadata`` so Alembic can detect model changes.
3. Supports both *offline* (URL only) and *online* (live connection) modes.
4. Uses the async SQLAlchemy engine (asyncpg driver) with ``run_sync`` so
   that Alembic's synchronous migration functions can run against the
   async engine without requiring a separate sync driver dependency.

Run from the ``backend/`` directory:

    alembic current
    alembic upgrade head
    alembic revision --autogenerate -m "add incidents table"
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Path setup — ensure ``backend/`` is on sys.path so ``app`` is importable
# ---------------------------------------------------------------------------
# alembic.ini sets ``prepend_sys_path = .`` (backend/), so this is
# typically a no-op, but we guard explicitly for safety.
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------
from app.config.settings import settings          # noqa: E402
from app.database.base import Base                # noqa: E402

# Import the models package so every table is registered with Base.metadata.
# Alembic's --autogenerate compares Base.metadata against the live schema
# to detect additions, removals, and column changes.
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Set the database URL from application settings (overrides alembic.ini value).
config.set_main_option("sqlalchemy.url", settings.async_database_url)

# Attach Python logging configuration from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for --autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.

    Useful for generating plain SQL scripts from migrations:

        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode (async)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Execute pending migrations against *connection* (sync context)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations via ``run_sync``.

    ``NullPool`` is used so that the engine disposes immediately after
    the migration run without lingering pooled connections.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
