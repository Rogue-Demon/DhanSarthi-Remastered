"""
Abstract base class and schemas for document text extraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    """Extracted text and structural elements of a single document page."""

    page_number: int = Field(..., description="1-indexed page number.")
    text: str = Field(..., description="Raw text content extracted from this page.")
    tables: List[List[List[str]]] = Field(
        default_factory=list,
        description="Structured tables found on this page. Formatted as List[Row[Cell]]."
    )


class ExtractionOutput(BaseModel):
    """Unified container representing extracted document data."""

    pages: List[PageContent] = Field(default_factory=list)
    raw_text: str = Field(..., description="Full concatenation of document text.")
    page_count: int = Field(..., description="Total pages processed.")
    ocr_required: bool = Field(
        default=False,
        description="True if document appears to be scanned/image-only and requires OCR."
    )


class DocumentTextExtractor(ABC):
    """Abstract interface for extracting text and tables from raw document bytes."""

    @abstractmethod
    def extract(self, data: bytes) -> ExtractionOutput:
        """
        Extract content from document raw binary.

        Args:
            data: Raw document file bytes.

        Returns:
            ExtractionOutput: Structured parsed contents.

        Raises:
            ExtractionFailedError: If parser fails or file is corrupted.
        """
        pass
