"""
Document ORM model.

A ``Document`` is a knowledge-base source file that is chunked, embedded,
and stored in ChromaDB for RAG retrieval (Milestone 3).  The ORM record
tracks metadata about each document; the actual vector embeddings live in
the ``embedding_metadata`` table.

Table: ``documents``
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DocumentCategory
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.embedding_metadata import EmbeddingMetadata


class Document(UUIDMixin, TimestampMixin, Base):
    """
    Metadata record for a RAG source document.

    Relationships:
        * ``embedding_metadata`` — one-to-many with
          :class:`~app.models.embedding_metadata.EmbeddingMetadata`.
          When a document is deleted all its chunk embeddings are removed too
          (``cascade="all, delete-orphan"``).

    Indexes:
        * ``category`` — used to filter documents by type during RAG retrieval.
    """

    __tablename__ = "documents"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Human-readable document title.",
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Origin URL or external reference of the document.",
    )
    category: Mapped[DocumentCategory] = mapped_column(
        SAEnum(DocumentCategory, name="documentcategory", create_constraint=True),
        nullable=False,
        index=True,
        doc="Classification used to filter relevant documents during RAG.",
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Filesystem path to the local copy of the document.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Short summary of the document's contents.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    #: All embedding chunks derived from this document.
    #: ``cascade="all, delete-orphan"`` — removing a document removes its
    #: embedding records from both PostgreSQL and must also purge the
    #: corresponding vectors from ChromaDB (handled by the service layer).
    #: ``lazy="select"`` — a document may have hundreds of chunks; load
    #: explicitly with ``selectinload`` when needed.
    embedding_metadata: Mapped[list["EmbeddingMetadata"]] = relationship(
        "EmbeddingMetadata",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Embedding chunk records for this document.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id!r} title={self.title!r} "
            f"category={self.category.value!r}>"
        )
