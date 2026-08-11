"""
PDF text extractor implementation using pypdf.
"""

from __future__ import annotations

import io
from pypdf import PdfReader
from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent
from app.documents.exceptions import ExtractionFailedError


class PDFDocumentExtractor(DocumentTextExtractor):
    """Parses text and basic page structure from machine-readable PDFs."""

    def extract(self, data: bytes) -> ExtractionOutput:
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = []
            full_text_parts = []
            ocr_required = True

            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                cleaned_text = text.strip()
                if cleaned_text:
                    ocr_required = False  # Found some text
                
                # Check for basic table-like structures if present
                # Standard pypdf doesn't support complex table extraction easily,
                # but we can initialize tables as empty list or parse simple layout.
                # In this phase, we keep tables empty and do text-based classification/extraction.
                pages.append(
                    PageContent(
                        page_number=idx,
                        text=cleaned_text,
                        tables=[]
                    )
                )
                full_text_parts.append(cleaned_text)

            # If pypdf couldn't find any pages or file is empty
            if not pages:
                raise ExtractionFailedError("PDF contains no readable pages.")

            # If all pages yield absolutely no text, we flag it as scanned/OCR required
            if ocr_required:
                # We do not fail the extraction, we set ocr_required=True to indicate it's scanned
                pass

            return ExtractionOutput(
                pages=pages,
                raw_text="\n--- PAGE BREAK ---\n".join(full_text_parts),
                page_count=len(pages),
                ocr_required=ocr_required
            )
        except Exception as exc:
            if isinstance(exc, ExtractionFailedError):
                raise
            raise ExtractionFailedError(f"Failed to parse PDF document: {str(exc)}") from exc
