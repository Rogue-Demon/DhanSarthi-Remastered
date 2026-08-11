"""
Financial Document Service.

Coordinates validation, storage, classification, extraction, normalization,
and validation checks for user financial documents.
"""

from __future__ import annotations

import datetime
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import DocumentStatus, DocumentType
from app.models.financial_document import FinancialDocument, DocumentExtraction
from app.repositories.document_repository import DocumentRepository, ExtractionRepository
from app.documents.exceptions import (
    DocumentAccessDeniedError,
    DuplicateDocumentError,
    ExtractionFailedError,
)
from app.documents.validation import FileValidator
from app.documents.storage.local import LocalDocumentStorage
from app.documents.extraction import get_extractor
from app.documents.classifier import DocumentClassifier
from app.documents.financial_extractor import FinancialDocumentExtractor
from app.documents.normalizer import FinancialDocumentNormalizer
from app.documents.validator import FinancialDocumentValidator


class DocumentService:
    """Coordinates lifecycle of user financial documents."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._doc_repo = DocumentRepository(db)
        self._ext_repo = ExtractionRepository(db)
        self._storage = LocalDocumentStorage(settings.document_storage_path)

        self._classifier = DocumentClassifier()
        self._extractor = FinancialDocumentExtractor()
        self._normalizer = FinancialDocumentNormalizer()
        self._validator = FinancialDocumentValidator()

    # ------------------------------------------------------------------
    # Document Upload & Retrieve
    # ------------------------------------------------------------------

    async def upload_document(
        self,
        user_id: int,
        filename: str,
        content_type: Optional[str],
        data: bytes,
    ) -> FinancialDocument:
        """
        Validate, hash, store, and record a new uploaded document.

        Raises DuplicateDocumentError if an identical file has been uploaded by the user.
        """
        # Run validations
        meta = FileValidator.validate_upload(filename, content_type, data)
        checksum = meta["checksum"]

        # Duplicate detection (user scoped)
        existing = self._doc_repo.find_by_checksum_for_user(user_id, checksum)
        if existing:
            raise DuplicateDocumentError(existing_id=existing.id)

        # Generate unique storage key
        storage_key = FileValidator.generate_storage_key(user_id, meta["extension"])

        # Construct model instance
        doc = FinancialDocument(
            user_id=user_id,
            original_filename=meta["sanitized_filename"],
            storage_key=storage_key,
            mime_type=meta["mime_type"],
            file_size=meta["file_size"],
            checksum=checksum,
            status=DocumentStatus.UPLOADED,
        )

        with handle_db_exceptions(resource="FinancialDocument"):
            # Save file data to storage asynchronously
            await self._storage.save(storage_key, data, meta["mime_type"])

            self._doc_repo.add(doc)
            self._db.commit()

        self._db.refresh(doc)
        return doc

    def list_documents(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[FinancialDocument], int]:
        """List user's uploaded documents."""
        items = self._doc_repo.list_for_user(user_id, skip=skip, limit=limit)
        total = self._doc_repo.count_for_user(user_id)
        return items, total

    def get_document(self, document_id: int, user_id: int) -> FinancialDocument:
        """Get document metadata with ownership verification."""
        doc = self._doc_repo.get_by_id(document_id)
        if doc is None or doc.status == DocumentStatus.REJECTED:
            raise ResourceNotFoundError(resource="FinancialDocument", identifier=document_id)
        if doc.user_id != user_id:
            raise DocumentAccessDeniedError()
        return doc

    async def delete_document(self, document_id: int, user_id: int) -> None:
        """Remove file from storage and mark document deleted in DB."""
        doc = self.get_document(document_id, user_id)
        
        with handle_db_exceptions(resource="FinancialDocument"):
            # Mark status as REJECTED (representing soft deletion)
            doc.status = DocumentStatus.REJECTED
            self._db.commit()

            # Async delete file from local storage
            await self._storage.delete(doc.storage_key)

    # ------------------------------------------------------------------
    # Document Analysis / Processing Pipeline
    # ------------------------------------------------------------------

    async def process_document(self, document_id: int, user_id: int) -> DocumentExtraction:
        """
        Execute parsing, classification, normalization, validation, and persist result.
        """
        doc = self.get_document(document_id, user_id)
        doc.status = DocumentStatus.PROCESSING
        self._db.commit()

        try:
            # 1. Retrieve file bytes from storage asynchronously
            data = await self._storage.get(doc.storage_key)

            # 2. Extract raw text structure
            extractor = get_extractor(doc.mime_type)
            extracted = extractor.extract(data)

            # 3. Classify document
            class_res = self._classifier.classify(extracted.raw_text)

            # 4. Extract structured fields / transactions
            info_res = self._extractor.extract_info(class_res.document_type, extracted)

            # 5. Normalize values
            self._normalizer.normalize(info_res)

            # 6. Check database & logic conflicts (Generate Warnings)
            warnings = self._validator.validate(self._db, user_id, info_res)

            # Clean old extraction records if reprocessing
            self._ext_repo.remove_for_document(document_id)

            # 7. Persist extraction candidate result
            # Convert fields and transactions to serializable JSON payloads
            serialized_fields = [f.model_dump(mode="json") for f in info_res.fields]
            serialized_txs = [t.model_dump(mode="json") for t in info_res.transactions]

            extraction_record = DocumentExtraction(
                document_id=document_id,
                extraction_version="1.0.0",
                document_type=class_res.document_type,
                classification_confidence=class_res.confidence,
                extracted_fields=serialized_fields,
                extracted_transactions=serialized_txs,
                warnings=warnings,
                raw_page_count=extracted.page_count,
                period_start=info_res.period_start,
                period_end=info_res.period_end,
            )

            # Update parent document type and status
            doc.document_type = class_res.document_type
            doc.processed_at = datetime.datetime.now(datetime.timezone.utc)
            doc.extractor_version = "1.0.0"
            
            # Determine appropriate final status
            if extracted.ocr_required:
                doc.status = DocumentStatus.REVIEW_REQUIRED
            elif warnings:
                doc.status = DocumentStatus.REVIEW_REQUIRED
            else:
                doc.status = DocumentStatus.EXTRACTED

            with handle_db_exceptions(resource="DocumentExtraction"):
                self._ext_repo.add(extraction_record)
                self._db.commit()

            self._db.refresh(extraction_record)
            return extraction_record

        except Exception as exc:
            # Mark processing as failed on exceptions
            doc.status = DocumentStatus.FAILED
            self._db.commit()
            if isinstance(exc, ExtractionFailedError):
                raise
            raise ExtractionFailedError(f"Document processing pipeline failed: {str(exc)}") from exc

    def get_extraction(self, document_id: int, user_id: int) -> DocumentExtraction:
        """Fetch extraction results for the given document."""
        # Enforce ownership check
        self.get_document(document_id, user_id)
        
        extraction = self._ext_repo.get_by_document_id(document_id)
        if extraction is None:
            raise ResourceNotFoundError(
                resource="DocumentExtraction",
                identifier=f"for document {document_id}"
            )
        return extraction
