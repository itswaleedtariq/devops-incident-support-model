"""
Database seed script.

Seeds the ``roles`` table with the four default application roles.
All seed operations are **idempotent** — safe to run multiple times without
creating duplicate records.

Usage (standalone):

    python -m app.database.seed

Usage (via CLI):

    python scripts/db.py seed
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.role import Role

logger = get_logger("database.seed")

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

#: Default roles created on first deploy.  Names are treated as unique keys;
#: existing records with the same name are left unchanged.
DEFAULT_ROLES: Final[list[dict[str, str]]] = [
    {
        "name": "Admin",
        "description": (
            "Full system access: manage users, roles, incidents, documents, "
            "and AI model configuration."
        ),
    },
    {
        "name": "DevOps Engineer",
        "description": (
            "Submit and manage incidents, view AI-generated remediation guidance, "
            "and access system monitoring dashboards."
        ),
    },
    {
        "name": "AI Engineer",
        "description": (
            "Manage RAG documents, review embedding metadata, monitor model "
            "performance, and access training data pipelines."
        ),
    },
    {
        "name": "Viewer",
        "description": (
            "Read-only access to incidents and AI-generated reports. "
            "Cannot submit or modify records."
        ),
    },
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


async def seed_roles(session: AsyncSession) -> int:
    """
    Create default roles that do not already exist.

    Args:
        session: An open ``AsyncSession`` (caller is responsible for commit).

    Returns:
        Number of roles created (0 if all already exist).
    """
    created = 0
    for role_data in DEFAULT_ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            role = Role(
                id=uuid.uuid4(),  # Explicit to avoid Python 3.14 default-callable issue
                name=role_data["name"],
                description=role_data["description"],
            )
            session.add(role)
            created += 1
            logger.info("  [+] Created role: '%s'", role_data["name"])
        else:
            logger.debug("  [=] Role '%s' already exists — skipped.", role_data["name"])

    return created


async def seed_database(session: AsyncSession) -> None:
    """
    Run all seed operations within a single session.

    Currently seeds: roles.
    Future milestones will extend this function with additional seed data.

    Args:
        session: An open ``AsyncSession``.  This function commits the session
                 after all seeds complete successfully.
    """
    logger.info("Starting database seed...")

    role_count = await seed_roles(session)

    await session.commit()

    logger.info(
        "Seed complete — %d role(s) created, %d role(s) already existed.",
        role_count,
        len(DEFAULT_ROLES) - role_count,
    )


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------


async def _run_seed() -> None:
    """Bootstrap DB connection and run the full seed."""
    from app.database.database import db_manager
    from app.database.session import get_session_factory

    await db_manager.connect()
    try:
        factory = get_session_factory(db_manager.engine)
        async with factory() as session:
            await seed_database(session)
    except Exception:
        logger.exception("Seed failed with an unhandled error.")
        raise
    finally:
        await db_manager.disconnect()


def run() -> None:
    """Synchronous entry point used by ``scripts/db.py`` and ``__main__``."""
    asyncio.run(_run_seed())


if __name__ == "__main__":
    run()
