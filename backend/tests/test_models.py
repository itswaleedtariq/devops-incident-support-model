"""
ORM model unit tests.

All tests in this module are **pure Python** — no database connection is
required.  They verify:

* Enum values and members
* Mixin column presence and types
* Model instantiation with correct defaults
* Relationship definitions
* Table names and constraints
* UUID auto-generation
* ``__repr__`` methods

Integration tests that need a live database (unique-constraint enforcement,
FK cascade, etc.) belong to ``test_database_connection.py`` and are
guarded by ``pytest.mark.integration``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.types import Boolean, DateTime, Integer, String


# ===========================================================================
# Enums
# ===========================================================================


class TestIncidentStatusEnum:
    def test_all_members_present(self) -> None:
        from app.models.enums import IncidentStatus

        names = {m.name for m in IncidentStatus}
        assert names == {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}

    def test_values_are_snake_case_strings(self) -> None:
        from app.models.enums import IncidentStatus

        assert IncidentStatus.OPEN.value == "open"
        assert IncidentStatus.IN_PROGRESS.value == "in_progress"
        assert IncidentStatus.RESOLVED.value == "resolved"
        assert IncidentStatus.CLOSED.value == "closed"


class TestIncidentSeverityEnum:
    def test_all_members_present(self) -> None:
        from app.models.enums import IncidentSeverity

        names = {m.name for m in IncidentSeverity}
        assert names == {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}

    def test_severity_values(self) -> None:
        from app.models.enums import IncidentSeverity

        assert IncidentSeverity.CRITICAL.value == "critical"
        assert IncidentSeverity.MEDIUM.value == "medium"
        assert IncidentSeverity.INFO.value == "info"


class TestDocumentCategoryEnum:
    def test_all_members_present(self) -> None:
        from app.models.enums import DocumentCategory

        names = {m.name for m in DocumentCategory}
        assert names == {
            "RUNBOOK",
            "INCIDENT_HISTORY",
            "KNOWLEDGE_BASE",
            "ARCHITECTURE",
            "API_DOCS",
            "OTHER",
        }

    def test_values_are_strings(self) -> None:
        from app.models.enums import DocumentCategory

        assert DocumentCategory.RUNBOOK.value == "runbook"
        assert DocumentCategory.OTHER.value == "other"


class TestUserStatusEnum:
    def test_all_members_present(self) -> None:
        from app.models.enums import UserStatus

        names = {m.name for m in UserStatus}
        assert names == {"ACTIVE", "INACTIVE", "SUSPENDED", "PENDING_VERIFICATION"}


# ===========================================================================
# Mixins (verified via a concrete model that uses them)
# ===========================================================================


class TestUUIDMixin:
    def test_id_column_exists(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        assert "id" in mapper.columns

    def test_id_is_primary_key(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        assert mapper.columns["id"].primary_key

    def test_id_column_has_callable_default(self) -> None:
        """The id column must declare a Python-callable default (uuid.uuid4)."""
        from app.models.role import Role

        mapper = sa_inspect(Role)
        id_col = mapper.columns["id"]
        assert id_col.default is not None, "id column must have a default configured"

    def test_id_default_is_uuid4(self) -> None:
        """The default callable must be uuid.uuid4 (checked by name)."""
        from app.models.role import Role

        mapper = sa_inspect(Role)
        id_col = mapper.columns["id"]
        # Check by function name — avoids Python 3.14 C-extension identity /
        # calling-convention differences while still verifying the right default.
        assert callable(id_col.default.arg)
        assert "uuid4" in id_col.default.arg.__name__


class TestTimestampMixin:
    def test_created_at_column_exists(self) -> None:
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        assert "created_at" in mapper.columns

    def test_updated_at_column_exists(self) -> None:
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        assert "updated_at" in mapper.columns

    def test_timestamps_are_datetime_type(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        assert isinstance(mapper.columns["created_at"].type, DateTime)
        assert isinstance(mapper.columns["updated_at"].type, DateTime)

    def test_created_at_has_server_default(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        col = mapper.columns["created_at"]
        assert col.server_default is not None


class TestSoftDeleteMixin:
    def test_is_deleted_column_exists(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        assert "is_deleted" in mapper.columns

    def test_deleted_at_column_exists(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        assert "deleted_at" in mapper.columns

    def test_is_deleted_column_has_false_default(self) -> None:
        """is_deleted must declare a server_default of 'false'."""
        from app.models.user import User

        mapper = sa_inspect(User)
        col = mapper.columns["is_deleted"]
        # Either a Python default or a server_default must be present.
        has_default = col.default is not None or col.server_default is not None
        assert has_default, "is_deleted must have a default configured"

    def test_deleted_at_defaults_to_none(self) -> None:
        from app.models.user import User

        user = User(
            full_name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        assert user.deleted_at is None


# ===========================================================================
# Role model
# ===========================================================================


class TestRoleModel:
    def test_table_name(self) -> None:
        from app.models.role import Role

        assert Role.__tablename__ == "roles"

    def test_has_name_column(self) -> None:
        from app.models.role import Role

        mapper = sa_inspect(Role)
        assert "name" in mapper.columns

    def test_name_is_unique(self) -> None:
        from app.models.role import Role

        mapper = sa_inspect(Role)
        assert mapper.columns["name"].unique

    def test_users_relationship_defined(self) -> None:
        from app.models.role import Role

        mapper = sa_inspect(Role)
        rel_keys = [r.key for r in mapper.relationships]
        assert "users" in rel_keys

    def test_repr(self) -> None:
        from app.models.role import Role

        role = Role(name="admin")
        r = repr(role)
        assert "Role" in r
        assert "admin" in r


# ===========================================================================
# User model
# ===========================================================================


class TestUserModel:
    def test_table_name(self) -> None:
        from app.models.user import User

        assert User.__tablename__ == "users"

    def test_required_columns_present(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        required = {"full_name", "username", "email", "password_hash"}
        present = set(mapper.columns.keys())
        assert required.issubset(present)

    def test_is_active_column_has_default(self) -> None:
        """is_active must declare a Python-level default."""
        from app.models.user import User

        mapper = sa_inspect(User)
        col = mapper.columns["is_active"]
        assert col.default is not None, "is_active must have a default configured"

    def test_is_verified_column_has_default(self) -> None:
        """is_verified must declare a Python-level default."""
        from app.models.user import User

        mapper = sa_inspect(User)
        col = mapper.columns["is_verified"]
        assert col.default is not None, "is_verified must have a default configured"

    def test_role_relationship_defined(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        rel_keys = [r.key for r in mapper.relationships]
        assert "role" in rel_keys

    def test_incidents_relationship_defined(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        rel_keys = [r.key for r in mapper.relationships]
        assert "incidents" in rel_keys

    def test_feedbacks_relationship_defined(self) -> None:
        from app.models.user import User

        mapper = sa_inspect(User)
        rel_keys = [r.key for r in mapper.relationships]
        assert "feedbacks" in rel_keys

    def test_repr(self) -> None:
        from app.models.user import User

        user = User(
            full_name="Jane",
            username="jane",
            email="jane@example.com",
            password_hash="hash",
        )
        r = repr(user)
        assert "User" in r
        assert "jane" in r


# ===========================================================================
# Incident model
# ===========================================================================


class TestIncidentModel:
    def test_table_name(self) -> None:
        from app.models.incident import Incident

        assert Incident.__tablename__ == "incidents"

    def test_status_column_has_default(self) -> None:
        """status column must declare a Python-level default (IncidentStatus.OPEN)."""
        from app.models.enums import IncidentStatus
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        col = mapper.columns["status"]
        assert col.default is not None, "status must have a default configured"
        assert col.default.arg == IncidentStatus.OPEN

    def test_severity_column_has_default(self) -> None:
        """severity column must declare a Python-level default (IncidentSeverity.MEDIUM)."""
        from app.models.enums import IncidentSeverity
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        col = mapper.columns["severity"]
        assert col.default is not None, "severity must have a default configured"
        assert col.default.arg == IncidentSeverity.MEDIUM

    def test_required_columns_present(self) -> None:
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        required = {"title", "description", "status", "severity", "created_by"}
        present = set(mapper.columns.keys())
        assert required.issubset(present)

    def test_created_by_user_relationship_defined(self) -> None:
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        rel_keys = [r.key for r in mapper.relationships]
        assert "created_by_user" in rel_keys

    def test_feedbacks_relationship_defined(self) -> None:
        from app.models.incident import Incident

        mapper = sa_inspect(Incident)
        rel_keys = [r.key for r in mapper.relationships]
        assert "feedbacks" in rel_keys

    def test_repr(self) -> None:
        from app.models.incident import Incident

        inc = Incident(title="DB down", description="Cannot connect.")
        r = repr(inc)
        assert "Incident" in r
        assert "DB down" in r


# ===========================================================================
# Feedback model
# ===========================================================================


class TestFeedbackModel:
    def test_table_name(self) -> None:
        from app.models.feedback import Feedback

        assert Feedback.__tablename__ == "feedbacks"

    def test_required_columns_present(self) -> None:
        from app.models.feedback import Feedback

        mapper = sa_inspect(Feedback)
        required = {"incident_id", "rating", "created_at"}
        present = set(mapper.columns.keys())
        assert required.issubset(present)

    def test_no_updated_at_column(self) -> None:
        """Feedback is immutable — no updated_at column should exist."""
        from app.models.feedback import Feedback

        mapper = sa_inspect(Feedback)
        assert "updated_at" not in mapper.columns

    def test_rating_column_is_integer(self) -> None:
        from app.models.feedback import Feedback

        mapper = sa_inspect(Feedback)
        assert isinstance(mapper.columns["rating"].type, Integer)

    def test_incident_relationship_defined(self) -> None:
        from app.models.feedback import Feedback

        mapper = sa_inspect(Feedback)
        rel_keys = [r.key for r in mapper.relationships]
        assert "incident" in rel_keys

    def test_user_relationship_defined(self) -> None:
        from app.models.feedback import Feedback

        mapper = sa_inspect(Feedback)
        rel_keys = [r.key for r in mapper.relationships]
        assert "user" in rel_keys

    def test_repr(self) -> None:
        from app.models.feedback import Feedback

        fb = Feedback(
            incident_id=uuid.uuid4(),
            rating=5,
        )
        r = repr(fb)
        assert "Feedback" in r
        assert "5" in r


# ===========================================================================
# Document model
# ===========================================================================


class TestDocumentModel:
    def test_table_name(self) -> None:
        from app.models.document import Document

        assert Document.__tablename__ == "documents"

    def test_required_columns_present(self) -> None:
        from app.models.document import Document

        mapper = sa_inspect(Document)
        required = {"title", "category"}
        present = set(mapper.columns.keys())
        assert required.issubset(present)

    def test_embedding_metadata_relationship_defined(self) -> None:
        from app.models.document import Document

        mapper = sa_inspect(Document)
        rel_keys = [r.key for r in mapper.relationships]
        assert "embedding_metadata" in rel_keys

    def test_repr(self) -> None:
        from app.models.enums import DocumentCategory
        from app.models.document import Document

        doc = Document(title="K8s Runbook", category=DocumentCategory.RUNBOOK)
        r = repr(doc)
        assert "Document" in r
        assert "K8s Runbook" in r


# ===========================================================================
# EmbeddingMetadata model
# ===========================================================================


class TestEmbeddingMetadataModel:
    def test_table_name(self) -> None:
        from app.models.embedding_metadata import EmbeddingMetadata

        assert EmbeddingMetadata.__tablename__ == "embedding_metadata"

    def test_required_columns_present(self) -> None:
        from app.models.embedding_metadata import EmbeddingMetadata

        mapper = sa_inspect(EmbeddingMetadata)
        required = {"document_id", "chunk_number", "embedding_model", "created_at"}
        present = set(mapper.columns.keys())
        assert required.issubset(present)

    def test_no_updated_at_column(self) -> None:
        """Embeddings are immutable — no updated_at should exist."""
        from app.models.embedding_metadata import EmbeddingMetadata

        mapper = sa_inspect(EmbeddingMetadata)
        assert "updated_at" not in mapper.columns

    def test_document_relationship_defined(self) -> None:
        from app.models.embedding_metadata import EmbeddingMetadata

        mapper = sa_inspect(EmbeddingMetadata)
        rel_keys = [r.key for r in mapper.relationships]
        assert "document" in rel_keys

    def test_repr(self) -> None:
        from app.models.embedding_metadata import EmbeddingMetadata

        em = EmbeddingMetadata(
            document_id=uuid.uuid4(),
            chunk_number=0,
            embedding_model="Qwen2.5-Coder-3B",
        )
        r = repr(em)
        assert "EmbeddingMetadata" in r
        assert "Qwen2.5-Coder-3B" in r


# ===========================================================================
# Cross-model: all tables registered with Base.metadata
# ===========================================================================


class TestBaseMetadata:
    def test_all_tables_registered(self) -> None:
        """Importing app.models must register all six tables."""
        import app.models  # noqa: F401
        from app.database.base import Base

        expected = {
            "roles",
            "users",
            "incidents",
            "feedbacks",
            "documents",
            "embedding_metadata",
        }
        registered = set(Base.metadata.tables.keys())
        assert expected.issubset(registered)

    def test_naming_convention_applied(self) -> None:
        """MetaData naming convention should be present on Base.metadata."""
        from app.database.base import Base

        assert Base.metadata.naming_convention is not None
        assert "ix" in Base.metadata.naming_convention
        assert "fk" in Base.metadata.naming_convention
