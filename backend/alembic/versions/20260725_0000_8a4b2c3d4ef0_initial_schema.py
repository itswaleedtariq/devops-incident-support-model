"""Initial schema — creates all application tables and PostgreSQL ENUM types.

Revision ID: 8a4b2c3d4ef0
Revises:
Create Date: 2026-07-25 00:00:00.000000

Tables created (in dependency order):
    roles, documents, users, incidents, feedbacks, embedding_metadata

PostgreSQL ENUM types created:
    incidentstatus, incidentseverity, documentcategory
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "8a4b2c3d4ef0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """Create all tables and ENUM types for the initial schema."""

    # -----------------------------------------------------------------------
    # PostgreSQL ENUM types
    # Must be created BEFORE any table that references them.
    # -----------------------------------------------------------------------
    op.execute(
        sa.text(
            "CREATE TYPE incidentstatus AS ENUM "
            "('open', 'in_progress', 'resolved', 'closed')"
        )
    )
    op.execute(
        sa.text(
            "CREATE TYPE incidentseverity AS ENUM "
            "('critical', 'high', 'medium', 'low', 'info')"
        )
    )
    op.execute(
        sa.text(
            "CREATE TYPE documentcategory AS ENUM "
            "('runbook', 'incident_history', 'knowledge_base', "
            " 'architecture', 'api_docs', 'other')"
        )
    )

    # -----------------------------------------------------------------------
    # roles
    # No foreign-key dependencies — must be created first.
    # -----------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    # Separate (non-unique) index for fast lookup by name.
    op.create_index("ix_roles_name", "roles", ["name"], unique=False)

    # -----------------------------------------------------------------------
    # documents
    # No foreign-key dependencies.
    # -----------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=1000), nullable=True),
        sa.Column(
            "category",
            # create_type=False — the ENUM was created explicitly above.
            sa.Enum(
                "runbook",
                "incident_history",
                "knowledge_base",
                "architecture",
                "api_docs",
                "other",
                name="documentcategory",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("path", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
    )
    op.create_index("ix_documents_category", "documents", ["category"], unique=False)

    # -----------------------------------------------------------------------
    # users
    # Depends on: roles
    # -----------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            # Python-level default only (no server_default in the model).
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column("role_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_users_role_id_roles",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        # Explicit unique constraints (defined in model's __table_args__).
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    # Non-unique indexes — complement the unique constraint indexes.
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)

    # -----------------------------------------------------------------------
    # incidents
    # Depends on: users
    # -----------------------------------------------------------------------
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("environment", sa.String(length=100), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "open", "in_progress", "resolved", "closed",
                name="incidentstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "critical", "high", "medium", "low", "info",
                name="incidentseverity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_incidents_created_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_incidents"),
    )
    op.create_index("ix_incidents_status", "incidents", ["status"], unique=False)
    op.create_index("ix_incidents_severity", "incidents", ["severity"], unique=False)
    op.create_index("ix_incidents_created_by", "incidents", ["created_by"], unique=False)
    # Composite index — optimises the common "open + critical" dashboard query.
    op.create_index(
        "ix_incidents_status_severity",
        "incidents",
        ["status", "severity"],
        unique=False,
    )

    # -----------------------------------------------------------------------
    # feedbacks
    # Depends on: incidents, users
    # -----------------------------------------------------------------------
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("incident_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # CHECK constraint: rating must be between 1 and 5.
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_feedbacks_rating_range",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name="fk_feedbacks_incident_id_incidents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_feedbacks_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feedbacks"),
    )
    op.create_index("ix_feedbacks_incident_id", "feedbacks", ["incident_id"], unique=False)
    op.create_index("ix_feedbacks_user_id", "feedbacks", ["user_id"], unique=False)

    # -----------------------------------------------------------------------
    # embedding_metadata
    # Depends on: documents
    # -----------------------------------------------------------------------
    op.create_table(
        "embedding_metadata",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("chunk_number", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=200), nullable=False),
        sa.Column("vector_id", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_embedding_metadata_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_embedding_metadata"),
        # Composite unique: one chunk record per position per document.
        sa.UniqueConstraint(
            "document_id",
            "chunk_number",
            name="uq_embedding_metadata_document_chunk",
        ),
    )
    op.create_index(
        "ix_embedding_metadata_document_id",
        "embedding_metadata",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_embedding_metadata_vector_id",
        "embedding_metadata",
        ["vector_id"],
        unique=False,
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """Drop all tables and ENUM types in reverse dependency order."""

    # -----------------------------------------------------------------------
    # Tables — drop leaf tables first to satisfy FK constraints.
    # -----------------------------------------------------------------------
    op.drop_index("ix_embedding_metadata_vector_id", table_name="embedding_metadata")
    op.drop_index("ix_embedding_metadata_document_id", table_name="embedding_metadata")
    op.drop_table("embedding_metadata")

    op.drop_index("ix_feedbacks_user_id", table_name="feedbacks")
    op.drop_index("ix_feedbacks_incident_id", table_name="feedbacks")
    op.drop_table("feedbacks")

    op.drop_index("ix_incidents_status_severity", table_name="incidents")
    op.drop_index("ix_incidents_created_by", table_name="incidents")
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_documents_category", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")

    # -----------------------------------------------------------------------
    # PostgreSQL ENUM types — drop after all referencing tables are gone.
    # -----------------------------------------------------------------------
    op.execute(sa.text("DROP TYPE IF EXISTS documentcategory"))
    op.execute(sa.text("DROP TYPE IF EXISTS incidentseverity"))
    op.execute(sa.text("DROP TYPE IF EXISTS incidentstatus"))
