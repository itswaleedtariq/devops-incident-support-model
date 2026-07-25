"""
ORM models package.

Importing this package registers all model tables with ``Base.metadata``,
which is required for Alembic's ``--autogenerate`` to detect schema changes.

Usage in application code::

    from app.models import Role, User, Incident, Feedback, Document, EmbeddingMetadata

Usage in Alembic ``env.py``::

    import app.models  # noqa: F401  — registers all tables
"""

from app.models.document import Document
from app.models.embedding_metadata import EmbeddingMetadata
from app.models.enums import (
    DocumentCategory,
    IncidentSeverity,
    IncidentStatus,
    UserStatus,
)
from app.models.feedback import Feedback
from app.models.incident import Incident
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.role import Role
from app.models.user import User

__all__ = [
    # Models
    "Role",
    "User",
    "Incident",
    "Feedback",
    "Document",
    "EmbeddingMetadata",
    # Enums
    "UserStatus",
    "IncidentStatus",
    "IncidentSeverity",
    "DocumentCategory",
    # Mixins
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
]

