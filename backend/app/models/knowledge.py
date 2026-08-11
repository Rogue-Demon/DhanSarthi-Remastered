"""
KnowledgeDocument and KnowledgeChunk models — general RAG knowledge store.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.vector_type import VectorType
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus
from app.models.mixins import TimestampMixin, pk_column


class KnowledgeDocument(Base, TimestampMixin):
    """An authoritative general financial document ingested into the RAG system.

    Examples: Tax Regulations 2026, RBI Loan Guidelines, AMFI Mutual Fund Handbook.

    This table stores document-level provenance, effective dates, source authority,
    and checksums for duplicate prevention. Personal user financial records
    must NEVER be stored in this table.
    """

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_documents_hash", "document_hash"),
        Index("ix_knowledge_documents_status_category", "status", "category"),
    )

    id: Mapped[int] = pk_column()
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    authority: Mapped[KnowledgeAuthority] = mapped_column(
        SAEnum(KnowledgeAuthority, native_enum=False, validate_strings=True, length=30),
        nullable=False,
        default=KnowledgeAuthority.GENERAL,
    )
    category: Mapped[KnowledgeCategory] = mapped_column(
        SAEnum(KnowledgeCategory, native_enum=False, validate_strings=True, length=30),
        nullable=False,
        default=KnowledgeCategory.GENERAL_FINANCE,
    )
    country: Mapped[str] = mapped_column(String(3), nullable=False, default="IND")
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False, default="India")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[KnowledgeDocumentStatus] = mapped_column(
        SAEnum(KnowledgeDocumentStatus, native_enum=False, validate_strings=True, length=20),
        nullable=False,
        default=KnowledgeDocumentStatus.ACTIVE,
    )

    chunks: Mapped[List[KnowledgeChunk]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument id={self.id} title={self.title!r} category={self.category}>"


class KnowledgeChunk(Base, TimestampMixin):
    """A semantic chunk of a KnowledgeDocument with an embedded vector for similarity search.

    The ``embedding`` column maps to pgvector's ``Vector(dim)`` type on PostgreSQL and
    JSON on SQLite.
    """

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        Index("ix_knowledge_chunks_doc_index", "document_id", "chunk_index"),
    )

    id: Mapped[int] = pk_column()
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(VectorType(dim=384), nullable=True)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    document: Mapped[KnowledgeDocument] = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk id={self.id} doc_id={self.document_id} index={self.chunk_index}>"
