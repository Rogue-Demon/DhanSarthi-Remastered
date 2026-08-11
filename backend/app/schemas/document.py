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


class ExtractionResponse(BaseModel):
    """Review schema exposing extracted metadata, candidates, and warnings."""

    model_config = ConfigDict(from_attributes=True)

    document_id: int
    document_type: DocumentType
    classification_confidence: float
    fields: List[ExtractedFieldSchema] = Field(default_factory=list)
    transactions: List[TransactionCandidateSchema] = Field(default_factory=list)
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


class ConfirmationResponse(BaseModel):
    """Import operation summary response."""

    imported_fields_count: int
    imported_transactions_count: int
    warnings: List[str] = Field(default_factory=list)
    status: DocumentStatus = Field(..., description="Updated status of the document.")
