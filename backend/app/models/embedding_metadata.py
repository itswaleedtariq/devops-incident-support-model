"""
EmbeddingMetadata ORM model.

Each ``EmbeddingMetadata`` record tracks one chunk of a source document
after it has been split, embedded, and stored in the ChromaDB vector store.

The ``vector_id`` column bridges the PostgreSQL record to its counterpart
in ChromaDB so the service layer can correlate retrieved vectors with their
originating documents.

Table: ``embedding_metadata``
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document


class EmbeddingMetadata(UUIDMixin, Base):
    """
    Tracks a single embedded text chunk from a :class:`~app.models.document.Document`.

    Relationships:
        * ``document`` — many-to-one with :class:`~app.models.document.Document`.
          Embedding records are cascade-deleted when the document is removed.

    Constraints:
        * ``(document_id, chunk_number)`` must be unique — a document cannot
          have two chunks with the same ordinal position.

    Note:
        This model stores *metadata* only.  The actual embedding vector lives
        in ChromaDB (Milestone 3) and is referenced via ``vector_id``.
    """

    __tablename__ = "embedding_metadata"

    __table_args__ = (
        # Guarantee one chunk record per position per document.
        UniqueConstraint(
            "document_id",
            "chunk_number",
            name="uq_embedding_metadata_document_chunk",
        ),
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
            name="fk_embedding_metadata_document_id_documents",
        ),
        nullable=False,
        index=True,
        doc="FK → documents.id.  Cascade-deletes this record when the document is removed.",
    )
    chunk_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Zero-based position of this chunk within the document.",
    )
    embedding_model: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Identifier of the model used to generate the embedding "
            "(e.g. 'Qwen2.5-Coder-3B-Instruct').",
    )
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        doc="Identifier of the corresponding vector in ChromaDB. "
            "``NULL`` until the embedding is persisted to the vector store.",
    )
    # Embedding records are created once and never updated — no updated_at.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp — set automatically when the chunk is embedded.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: The source document this chunk belongs to.
    #: ``lazy="selectin"`` — document metadata is almost always needed
    #: when working with an embedding record.
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="embedding_metadata",
        lazy="selectin",
        doc="Source document that produced this embedding chunk.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<EmbeddingMetadata id={self.id!r} document_id={self.document_id!r} "
            f"chunk={self.chunk_number!r} model={self.embedding_model!r}>"
        )
