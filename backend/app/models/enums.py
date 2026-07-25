"""
Application-wide SQLAlchemy-compatible enums.

Each enum is backed by a native PostgreSQL ``ENUM`` type via
``sqlalchemy.Enum``, giving strong type safety at both the Python and
database level.

Enum classes are imported by model modules and Pydantic schemas.
"""

from __future__ import annotations

import enum


class UserStatus(enum.Enum):
    """
    Lifecycle status of a user account.

    Used in business-logic rules (e.g. blocking logins for SUSPENDED accounts).
    Not yet mapped to a column; reserved for Milestone 2.3+.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class IncidentStatus(enum.Enum):
    """
    Represents the current resolution stage of an incident.

    State machine:
        OPEN → IN_PROGRESS → RESOLVED → CLOSED
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(enum.Enum):
    """
    Business-impact severity of an incident.

    Ordered from highest to lowest impact:
        CRITICAL > HIGH > MEDIUM > LOW > INFO
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentCategory(enum.Enum):
    """
    Classifies RAG source documents for targeted retrieval.

    Used by the vector store to filter relevant context chunks
    per query type (Milestone 3+).
    """

    RUNBOOK = "runbook"
    INCIDENT_HISTORY = "incident_history"
    KNOWLEDGE_BASE = "knowledge_base"
    ARCHITECTURE = "architecture"
    API_DOCS = "api_docs"
    OTHER = "other"
