"""
Repository dependency providers.

Each function is a FastAPI ``Depends`` callable that binds a repository
to the current request-scoped ``AsyncSession``.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_role_repository(session: AsyncSession = Depends(get_db)) -> RoleRepository:
    return RoleRepository(session)


def get_incident_repository(session: AsyncSession = Depends(get_db)) -> IncidentRepository:
    return IncidentRepository(session)


def get_feedback_repository(session: AsyncSession = Depends(get_db)) -> FeedbackRepository:
    return FeedbackRepository(session)


def get_document_repository(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(session)


def get_embedding_repository(session: AsyncSession = Depends(get_db)) -> EmbeddingRepository:
    return EmbeddingRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)
