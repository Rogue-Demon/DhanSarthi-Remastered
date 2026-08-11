"""
Plain text document extractor implementation.
"""

from __future__ import annotations

from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent
from app.documents.exceptions import ExtractionFailedError


class TextDocumentExtractor(DocumentTextExtractor):
    """Parses plain text (.txt) files."""

    def extract(self, data: bytes) -> ExtractionOutput:
        try:
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                decoded = data.decode("latin-1")

            cleaned = decoded.strip()
            if not cleaned:
                raise ExtractionFailedError("Plain text document is empty.")

            page = PageContent(
                page_number=1,
                text=cleaned,
                tables=[]
            )

            return ExtractionOutput(
                pages=[page],
                raw_text=cleaned,
                page_count=1,
                ocr_required=False
            )
        except Exception as exc:
            if isinstance(exc, ExtractionFailedError):
                raise
            raise ExtractionFailedError(f"Failed to parse text document: {str(exc)}") from exc
