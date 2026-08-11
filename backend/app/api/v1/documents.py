"""
FastAPI router for DhanSarthi Document Intelligence.

Exposes endpoints for uploading, listing, analyzing, reviewing, confirming,
and deleting user financial documents.
All routes require valid JWT authentication.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import (
    get_document_service,
    get_document_import_service,
    get_current_user_id,
)
from app.schemas.document import (
    ConfirmationRequest,
    ConfirmationResponse,
    DocumentListResponse,
    DocumentResponse,
    ExtractionResponse,
    ExtractedFieldSchema,
    TransactionCandidateSchema,
)
from app.services.document_service import DocumentService
from app.services.document_import_service import FinancialDocumentImportService

router = APIRouter(prefix="/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# Document Lifecycle & Retrieval
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a financial document",
)
async def upload_document(
    file: UploadFile = File(..., description="The financial document to upload (PDF, CSV, JPEG, PNG, TXT)."),
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """
    Upload and securely store a user financial document.

    Run validations (magic bytes, size) and generate checksums.
    """
    file_bytes = await file.read()
    doc = await doc_service.upload_document(
        user_id=user_id,
        filename=file.filename or "uploaded_file",
        content_type=file.content_type,
        data=file_bytes
    )
    return DocumentResponse.model_validate(doc)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
)
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """Retrieve a paginated list of the current user's documents."""
    items, total = doc_service.list_documents(user_id=user_id, skip=skip, limit=limit)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata",
)
def get_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get metadata for a single document. Enforces user isolation ownership checks."""
    doc = doc_service.get_document(document_id=document_id, user_id=user_id)
    return DocumentResponse.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an uploaded document",
)
async def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> None:
    """
    Soft-delete a document record and permanently erase the file from storage.

    Does not modify already imported authoritative records.
    """
    await doc_service.delete_document(document_id=document_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Processing & Extraction Review
# ---------------------------------------------------------------------------


@router.post(
    "/{document_id}/process",
    response_model=ExtractionResponse,
    summary="Process document",
)
async def process_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> ExtractionResponse:
    """
    Run the processing and extraction pipeline on an uploaded document.

    Categorizes the document and extracts transaction/metadata fields.
    """
    extraction = await doc_service.process_document(document_id=document_id, user_id=user_id)
    
    # Map model attributes to list representation schemas
    fields_list = [ExtractedFieldSchema.model_validate(f) for f in (extraction.extracted_fields or [])]
    txs_list = [TransactionCandidateSchema.model_validate(t) for t in (extraction.extracted_transactions or [])]

    return ExtractionResponse(
        document_id=extraction.document_id,
        document_type=extraction.document_type,
        classification_confidence=extraction.classification_confidence or 0.0,
        fields=fields_list,
        transactions=txs_list,
        warnings=extraction.warnings or [],
        raw_page_count=extraction.raw_page_count or 1,
        period_start=extraction.period_start,
        period_end=extraction.period_end,
        ocr_required=extraction.document.status == "REVIEW_REQUIRED" and not extracted_text_found(extraction)
    )


@router.get(
    "/{document_id}/extraction",
    response_model=ExtractionResponse,
    summary="Get extraction results",
)
def get_extraction(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> ExtractionResponse:
    """Get the extracted fields and transaction candidates for user review."""
    extraction = doc_service.get_extraction(document_id=document_id, user_id=user_id)
    
    fields_list = [ExtractedFieldSchema.model_validate(f) for f in (extraction.extracted_fields or [])]
    txs_list = [TransactionCandidateSchema.model_validate(t) for t in (extraction.extracted_transactions or [])]

    return ExtractionResponse(
        document_id=extraction.document_id,
        document_type=extraction.document_type,
        classification_confidence=extraction.classification_confidence or 0.0,
        fields=fields_list,
        transactions=txs_list,
        warnings=extraction.warnings or [],
        raw_page_count=extraction.raw_page_count or 1,
        period_start=extraction.period_start,
        period_end=extraction.period_end,
        ocr_required=extraction.document.status == "REVIEW_REQUIRED" and not extracted_text_found(extraction)
    )


# ---------------------------------------------------------------------------
# Import / Confirmation
# ---------------------------------------------------------------------------


@router.post(
    "/{document_id}/confirm",
    response_model=ConfirmationResponse,
    summary="Confirm extraction and import records",
)
def confirm_extraction(
    document_id: int,
    req: ConfirmationRequest,
    user_id: int = Depends(get_current_user_id),
    import_service: FinancialDocumentImportService = Depends(get_document_import_service),
) -> ConfirmationResponse:
    """
    User-confirmed import of selected extraction fields and transactions.

    Imports items into authoritative tables (Income, Transaction) via domain services.
    """
    return import_service.confirm_and_import(
        document_id=document_id,
        user_id=user_id,
        req=req,
    )


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def extracted_text_found(extraction) -> bool:
    """Checks if text content was successfully recovered during parsing."""
    # If the document status is review required, but we extracted fields, it is not OCR required.
    return bool(extraction.extracted_fields) or bool(extraction.extracted_transactions)
