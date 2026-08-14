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
    return _build_extraction_response(extraction)


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
    return _build_extraction_response(extraction)


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


def _build_extraction_response(extraction) -> ExtractionResponse:
    import datetime
    import re
    from decimal import Decimal
    from app.models.enums import DocumentType
    from app.documents.mapping_registry import default_mapping_registry
    from app.schemas.document import (
        IncomeCandidateSchema,
        ExpenseCandidateSchema,
        AssetCandidateSchema,
        LiabilityCandidateSchema,
        MappedFieldExplanationSchema,
    )

    candidate_field_names = {"net_salary", "total_amount", "amount_due", "outstanding_balance", "current_value"}
    fields_list = [
        ExtractedFieldSchema.model_validate(f)
        for f in (extraction.extracted_fields or [])
        if f["name"] not in candidate_field_names
    ]
    txs_list = [TransactionCandidateSchema.model_validate(t) for t in (extraction.extracted_transactions or [])]

    fields_map = {f["name"]: f for f in (extraction.extracted_fields or [])}
    doc_type = extraction.document_type

    income_candidates = []
    expense_candidates = []
    asset_candidates = []
    liability_candidates = []
    field_explanations = []

    # Salary Slip candidate construction
    if doc_type == DocumentType.SALARY_SLIP:
        if "net_salary" in fields_map:
            net_val = Decimal(str(fields_map["net_salary"]["value"]))
            emp_val = fields_map.get("employer", {}).get("value", "Employer")
            
            p_end = extraction.period_end
            if not p_end and "salary_period" in fields_map:
                p_str = str(fields_map["salary_period"].get("value", ""))
                m = re.search(r"([a-zA-Z]+)\s*(\d{4})", p_str)
                if m:
                    month_names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                    m_prefix = m.group(1).lower()[:3]
                    yr = int(m.group(2))
                    if m_prefix in month_names:
                        m_idx = month_names.index(m_prefix) + 1
                        p_end = datetime.date(yr, m_idx, 1)

            if not p_end:
                p_end = datetime.date.today()

            income_candidates.append(
                IncomeCandidateSchema(
                    candidate_id="net_salary",
                    source=f"Salary ({emp_val})" if emp_val != "Employer" else "Salary Slip Import",
                    amount=net_val,
                    income_date=p_end,
                    category="Salary",
                    description="Imported Net Salary from document"
                )
            )

    # Bill candidate construction
    elif doc_type == DocumentType.BILL:
        if "total_amount" in fields_map:
            tot_val = Decimal(str(fields_map["total_amount"]["value"]))
            vendor_val = fields_map.get("vendor", {}).get("value", "Biller")
            b_date = extraction.period_end or datetime.date.today()
            expense_candidates.append(
                ExpenseCandidateSchema(
                    candidate_id="total_amount",
                    merchant=vendor_val,
                    amount=tot_val,
                    expense_date=b_date,
                    category="Utilities",
                    description="Imported Utility Bill"
                )
            )

    # Loan Statement candidate construction
    elif doc_type == DocumentType.LOAN_STATEMENT:
        if "outstanding_balance" in fields_map:
            bal_val = Decimal(str(fields_map["outstanding_balance"]["value"]))
            lender_val = fields_map.get("lender", {}).get("value", "Lender")
            rate_val = fields_map.get("interest_rate", {}).get("value")
            rate_dec = Decimal(str(rate_val)) if rate_val else None
            liability_candidates.append(
                LiabilityCandidateSchema(
                    candidate_id="outstanding_balance",
                    name=f"Loan ({lender_val})" if lender_val != "Lender" else "Loan Obligation",
                    amount=bal_val,
                    liability_type="PERSONAL_DEBT",
                    interest_rate=rate_dec,
                    institution=lender_val if lender_val != "Lender" else None
                )
            )

    # Investment Statement candidate construction
    elif doc_type == DocumentType.INVESTMENT_STATEMENT:
        if "current_value" in fields_map:
            val = Decimal(str(fields_map["current_value"]["value"]))
            scheme_val = fields_map.get("scheme_name", {}).get("value", "Investment Portfolio")
            asset_candidates.append(
                AssetCandidateSchema(
                    candidate_id="current_value",
                    name=scheme_val,
                    value=val,
                    asset_type="BANK_BALANCE",
                    description="Imported Holding"
                )
            )

    # Field explanations
    for f in (extraction.extracted_fields or []):
        f_name = f["name"]
        rule = default_mapping_registry.get_rule(doc_type, f_name)
        field_explanations.append(
            MappedFieldExplanationSchema(
                field_name=f_name,
                status="SUPPORTED" if rule.behavior != "UNSUPPORTED" else "UNSUPPORTED",
                destination=rule.destination_type.value,
                explanation=rule.explanation
            )
        )

    return ExtractionResponse(
        document_id=extraction.document_id,
        document_type=extraction.document_type,
        classification_confidence=extraction.classification_confidence or 0.0,
        fields=fields_list,
        transactions=txs_list,
        income_candidates=income_candidates,
        expense_candidates=expense_candidates,
        asset_candidates=asset_candidates,
        liability_candidates=liability_candidates,
        field_explanations=field_explanations,
        warnings=extraction.warnings or [],
        raw_page_count=extraction.raw_page_count or 1,
        period_start=extraction.period_start,
        period_end=extraction.period_end,
        ocr_required=extraction.document.status == "REVIEW_REQUIRED" and not extracted_text_found(extraction),
    )
