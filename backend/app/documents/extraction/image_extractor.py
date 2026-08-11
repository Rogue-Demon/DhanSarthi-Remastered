"""
Image document extractor stub (place-holder for future OCR provider).
"""

from __future__ import annotations

from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent


class ImageDocumentExtractor(DocumentTextExtractor):
    """Placeholder for OCR extraction. Always flags document as requiring OCR."""

    def extract(self, data: bytes) -> ExtractionOutput:
        # Images cannot be parsed deterministically without an OCR engine like Tesseract.
        # We return a structured output highlighting that OCR is required.
        page = PageContent(
            page_number=1,
            text="",
            tables=[]
        )
        return ExtractionOutput(
            pages=[page],
            raw_text="",
            page_count=1,
            ocr_required=True
        )
