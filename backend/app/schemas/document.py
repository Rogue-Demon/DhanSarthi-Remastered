"""
Pydantic schemas for DhanSarthi Document Intelligence.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    """Public representation of a financial document's metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    storage_key: str
    mime_type: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus
    checksum: str
    extractor_version: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Paginated collection of user's financial documents."""

    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class ExtractedFieldSchema(BaseModel):
    """Schema for metadata fields extracted from a document."""

    name: str = Field(..., description="Field identifier (e.g. net_salary, emi).")
    value: Any = Field(..., description="Normalized field value.")
    confidence: float = Field(..., description="Extraction confidence (0.0 to 1.0).")
    source_page: int = Field(1, description="Page number of extraction source.")
    source_text_ref: Optional[str] = Field(None, description="Verbatim text context matching extraction.")


class TransactionCandidateSchema(BaseModel):
    """Schema for bank statement transaction candidates awaiting user review."""

    candidate_id: str = Field(..., description="Unique generated key for selective confirmation.")
    date: str = Field(..., description="Transaction date (ISO formatted).")
    description: str = Field(..., description="Description / Narration.")
    debit: Optional[str] = Field(None, description="Debit amount (as string for formatting).")
    credit: Optional[str] = Field(None, description="Credit amount (as string for formatting).")
    balance: Optional[str] = Field(None, description="Running balance (as string for formatting).")
    currency: str = Field("INR", description="Three-letter currency code.")
    source_page: int = 1
    source_row: int = 0
    confidence: float = 1.0


class IncomeCandidateSchema(BaseModel):
    """Candidate schema for Income creation."""

    candidate_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    source: str
    amount: Decimal
    income_date: date
    category: str = "Salary"
    currency: str = "INR"
    frequency: str = "MONTHLY"
    description: Optional[str] = None
    confidence: float = 1.0


class ExpenseCandidateSchema(BaseModel):
    """Candidate schema for Expense creation."""

    candidate_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    merchant: str
    amount: Decimal
    expense_date: date
    category: str = "Utilities"
    currency: str = "INR"
    description: Optional[str] = None
    confidence: float = 1.0


class AssetCandidateSchema(BaseModel):
    """Candidate schema for Asset creation."""

    candidate_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    name: str
    value: Decimal
    asset_type: str = "BANK_BALANCE"
    institution: Optional[str] = None
    maturity_date: Optional[date] = None
    description: Optional[str] = None
    confidence: float = 1.0


class LiabilityCandidateSchema(BaseModel):
    """Candidate schema for Liability creation."""

    candidate_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    name: str
    amount: Decimal
    liability_type: str = "PERSONAL_DEBT"
    interest_rate: Optional[Decimal] = None
    monthly_payment: Optional[Decimal] = None
    institution: Optional[str] = None
    description: Optional[str] = None
    confidence: float = 1.0


class MappedFieldExplanationSchema(BaseModel):
    """Explanation schema reporting how an extracted field was mapped or why it was skipped."""

    field_name: str
    status: str = Field(..., description="Field status (SUPPORTED, IMPORTED, SKIPPED, REVIEW_ONLY, UNSUPPORTED, DUPLICATE)")
    destination: str = Field(..., description="Financial destination (INCOME, EXPENSE, ASSET, LIABILITY, METADATA, REVIEW_ONLY, UNSUPPORTED)")
    explanation: str = Field(..., description="Human-readable reason description.")


class ExtractionResponse(BaseModel):
    """Review schema exposing extracted metadata, candidates, and warnings."""

    model_config = ConfigDict(from_attributes=True)

    document_id: int
    document_type: DocumentType
    classification_confidence: float
    fields: List[ExtractedFieldSchema] = Field(default_factory=list)
    transactions: List[TransactionCandidateSchema] = Field(default_factory=list)
    income_candidates: List[IncomeCandidateSchema] = Field(default_factory=list)
    expense_candidates: List[ExpenseCandidateSchema] = Field(default_factory=list)
    asset_candidates: List[AssetCandidateSchema] = Field(default_factory=list)
    liability_candidates: List[LiabilityCandidateSchema] = Field(default_factory=list)
    field_explanations: List[MappedFieldExplanationSchema] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw_page_count: int = 1
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    ocr_required: bool = Field(default=False, description="True if PDF requires OCR parsing.")


class ConfirmationRequest(BaseModel):
    """Selected field and transaction candidates approved by user for DB import."""

    confirmed_fields: List[str] = Field(
        default_factory=list,
        description="Names of metadata fields to import (e.g. ['net_salary'])."
    )
    confirmed_transactions: List[str] = Field(
        default_factory=list,
        description="UUID candidate_ids of transactions to import."
    )
    confirmed_income: List[IncomeCandidateSchema] = Field(
        default_factory=list,
        description="Approved Income candidate objects."
    )
    confirmed_expenses: List[ExpenseCandidateSchema] = Field(
        default_factory=list,
        description="Approved Expense candidate objects."
    )
    confirmed_assets: List[AssetCandidateSchema] = Field(
        default_factory=list,
        description="Approved Asset candidate objects."
    )
    confirmed_liabilities: List[LiabilityCandidateSchema] = Field(
        default_factory=list,
        description="Approved Liability candidate objects."
    )


class ConfirmationResponse(BaseModel):
    """Import operation summary response."""

    imported_fields_count: int
    imported_transactions_count: int
    imported_income_count: int = 0
    imported_expense_count: int = 0
    imported_asset_count: int = 0
    imported_liability_count: int = 0
    imported_metadata_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    field_explanations: List[MappedFieldExplanationSchema] = Field(default_factory=list)
    status: DocumentStatus = Field(..., description="Updated status of the document.")

