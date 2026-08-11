"""
CSV table and text extractor implementation.
"""

from __future__ import annotations

import csv
import io
from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent
from app.documents.exceptions import ExtractionFailedError


class CSVDocumentExtractor(DocumentTextExtractor):
    """Parses text and structured tables from CSV spreadsheets."""

    def extract(self, data: bytes) -> ExtractionOutput:
        try:
            # Decode bytes using utf-8 with fallback to latin-1
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                decoded = data.decode("latin-1")

            reader = csv.reader(io.StringIO(decoded))
            rows = []
            for row in reader:
                rows.append([cell.strip() for cell in row])

            if not rows:
                raise ExtractionFailedError("CSV document is empty.")

            # Format the text preview and table structure
            text_lines = []
            for row in rows:
                text_lines.append(" | ".join(row))
            raw_text = "\n".join(text_lines)

            # CSV is treated as a single page document containing one table
            page = PageContent(
                page_number=1,
                text=raw_text,
                tables=[rows]
            )

            return ExtractionOutput(
                pages=[page],
                raw_text=raw_text,
                page_count=1,
                ocr_required=False
            )
        except Exception as exc:
            if isinstance(exc, ExtractionFailedError):
                raise
            raise ExtractionFailedError(f"Failed to parse CSV document: {str(exc)}") from exc
