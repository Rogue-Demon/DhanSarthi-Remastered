"""
Document and DocumentExtraction database repositories.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.financial_document import FinancialDocument, DocumentExtraction
from app.models.enums import DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[FinancialDocument]):
    """Database access methods for FinancialDocument."""

    def __init__(self, db: Session) -> None:
        super().__init__(FinancialDocument, db)

    def get_by_id_for_user(self, document_id: int, user_id: int) -> Optional[FinancialDocument]:
        """Fetch a document by ID and verify ownership."""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.id == document_id)
            .where(FinancialDocument.user_id == user_id)
            .where(FinancialDocument.status != DocumentStatus.REJECTED)  # Or represent deleted state
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def find_by_checksum_for_user(self, user_id: int, checksum: str) -> Optional[FinancialDocument]:
        """Look for an existing document with matching checksum for duplicate detection."""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.user_id == user_id)
            .where(FinancialDocument.checksum == checksum)
            .where(FinancialDocument.status != DocumentStatus.REJECTED)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[FinancialDocument]:
        """Fetch paginated documents for the given user, newest first."""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.user_id == user_id)
            .where(FinancialDocument.status != DocumentStatus.REJECTED)
            .order_by(FinancialDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

    def count_for_user(self, user_id: int) -> int:
        """Count non-deleted documents for the user."""
        stmt = (
            select(func.count())
            .select_from(FinancialDocument)
            .where(FinancialDocument.user_id == user_id)
            .where(FinancialDocument.status != DocumentStatus.REJECTED)
        )
        return self._db.execute(stmt).scalar_one()


class ExtractionRepository(BaseRepository[DocumentExtraction]):
    """Database access methods for DocumentExtraction."""

    def __init__(self, db: Session) -> None:
        super().__init__(DocumentExtraction, db)

    def get_by_document_id(self, document_id: int) -> Optional[DocumentExtraction]:
        """Fetch latest extraction record associated with the document."""
        stmt = (
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document_id)
            .order_by(DocumentExtraction.created_at.desc())
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def remove_for_document(self, document_id: int) -> None:
        """Delete all extraction rows associated with a document (useful for reprocessing)."""
        stmt = select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
        records = self._db.execute(stmt).scalars().all()
        for r in records:
            self._db.delete(r)
        self._db.flush()
