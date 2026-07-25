"""
Repositories package (data-access layer).

Public exports for convenient importing.
"""

from app.repositories.base import BaseRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "IncidentRepository",
    "FeedbackRepository",
    "DocumentRepository",
    "EmbeddingRepository",
    "RefreshTokenRepository",
]
