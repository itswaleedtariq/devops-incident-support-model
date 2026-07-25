"""Embedding metadata repository."""

from __future__ import annotations

from app.models.embedding_metadata import EmbeddingMetadata
from app.repositories.base import BaseRepository


class EmbeddingRepository(BaseRepository[EmbeddingMetadata]):
    """Data-access operations for :class:`~app.models.embedding_metadata.EmbeddingMetadata`."""

    model = EmbeddingMetadata
