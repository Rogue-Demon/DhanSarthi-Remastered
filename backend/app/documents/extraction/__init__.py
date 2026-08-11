"""
Document extractor factory registry.
"""

from __future__ import annotations

from app.documents.exceptions import UnsupportedFileTypeError
from app.documents.extraction.base import DocumentTextExtractor
from app.documents.extraction.pdf_extractor import PDFDocumentExtractor
from app.documents.extraction.csv_extractor import CSVDocumentExtractor
from app.documents.extraction.text_extractor import TextDocumentExtractor
from app.documents.extraction.image_extractor import ImageDocumentExtractor


def get_extractor(mime_type: str) -> DocumentTextExtractor:
    """
    Return the appropriate extractor for the given MIME type.

    Args:
        mime_type: The validated MIME type.

    Returns:
        DocumentTextExtractor: The concrete extractor implementation.

    Raises:
        UnsupportedFileTypeError: If no extractor exists for the MIME type.
    """
    m = mime_type.lower()
    if m == "application/pdf":
        return PDFDocumentExtractor()
    elif m in ("text/csv", "application/csv"):
        return CSVDocumentExtractor()
    elif m == "text/plain":
        return TextDocumentExtractor()
    elif m in ("image/png", "image/jpeg"):
        return ImageDocumentExtractor()
    else:
        raise UnsupportedFileTypeError(mime_type)
