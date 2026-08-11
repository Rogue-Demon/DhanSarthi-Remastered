"""
FinancialDocument and DocumentExtraction models for DhanSarthi Document Intelligence.

Each FinancialDocument belongs to exactly one authenticated user.
DocumentExtraction stores the structured extraction result from processing.

Security invariants:
  - FinancialDocument.user_id enforces ownership scoping.
  - Documents are never publicly accessible.
  - storage_key is UUID-based — never derived from original_filename.
  - checksum (SHA-256) enables duplicate detection per user.
  - Extraction data is NOT authoritative until user confirms it.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DocumentStatus, DocumentType
from app.models.mixins import TimestampMixin, pk_column


class FinancialDocument(Base, TimestampMixin):
    """A user-uploaded financial document (bank statement, salary slip, etc.).

    The file itself is stored externally via DocumentStorage.
    Only metadata and the storage_key reference are persisted here.
    """

    __tablename__ = "financial_documents"
    __table_args__ = (
        Index("ix_fin_docs_user_id", "user_id"),
        Index("ix_fin_docs_status", "status"),
        UniqueConstraint("user_id", "checksum", name="uq_fin_docs_user_checksum"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, native_enum=False, validate_strings=True, length=30),
        nullable=False,
        default=DocumentType.UNKNOWN,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, native_enum=False, validate_strings=True, length=20),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    extractions: Mapped[List["DocumentExtraction"]] = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentExtraction.created_at.desc()",
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialDocument id={self.id} user_id={self.user_id} "
            f"type={self.document_type} status={self.status}>"
        )


class DocumentExtraction(Base, TimestampMixin):
    """Structured extraction result from processing a FinancialDocument.

    extracted_fields: JSON array of typed field extractions with confidence.
    extracted_transactions: JSON array of transaction candidates with confidence.
    warnings: JSON array of validation warnings/conflicts.

    This data is NOT authoritative. User must explicitly confirm before import.
    """

    __tablename__ = "document_extractions"
    __table_args__ = (
        Index("ix_doc_extractions_document_id", "document_id"),
    )

    id: Mapped[int] = pk_column()
    document_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("financial_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1.0.0"
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, native_enum=False, validate_strings=True, length=30),
        nullable=False,
        default=DocumentType.UNKNOWN,
    )
    classification_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    extracted_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extracted_transactions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    raw_page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    document: Mapped[FinancialDocument] = relationship(
        "FinancialDocument",
        back_populates="extractions",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentExtraction id={self.id} doc_id={self.document_id} "
            f"type={self.document_type} confidence={self.classification_confidence}>"
        )
