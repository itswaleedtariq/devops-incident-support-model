"""Document repository."""

from __future__ import annotations

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Data-access operations for the :class:`~app.models.document.Document` model."""

    model = Document
