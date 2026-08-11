"""
Document Intelligence exception hierarchy.

All exceptions inherit from DhanSarthiError so they are handled
by the application-wide exception handlers in main.py.
"""

from __future__ import annotations

from app.core.exceptions import DhanSarthiError


class DocumentError(DhanSarthiError):
    """Base exception for all document intelligence operations."""
    pass


class UnsupportedFileTypeError(DocumentError):
    """File type/MIME is not in the allowed list."""

    def __init__(self, mime_type: str = "unknown") -> None:
        self.mime_type = mime_type
        super().__init__(f"Unsupported file type: {mime_type}")


class FileTooLargeError(DocumentError):
    """File exceeds the configured maximum upload size."""

    def __init__(self, size_mb: float, max_mb: int) -> None:
        self.size_mb = size_mb
        self.max_mb = max_mb
        super().__init__(
            f"File size ({size_mb:.1f} MB) exceeds the maximum allowed size ({max_mb} MB)."
        )


class InvalidDocumentError(DocumentError):
    """Document content is invalid, corrupt, or has mismatched signature."""
    pass


class DocumentAccessDeniedError(DocumentError):
    """User attempted to access a document they do not own."""

    def __init__(self) -> None:
        super().__init__("Access denied. This document does not belong to you.")


class ExtractionFailedError(DocumentError):
    """Document extraction (text/table) failed."""
    pass


class ClassificationFailedError(DocumentError):
    """Document classification could not determine a document type."""
    pass


class ConfirmationInvalidError(DocumentError):
    """Confirmation request is invalid (wrong state, already confirmed, etc.)."""
    pass


class DuplicateDocumentError(DocumentError):
    """User uploaded an identical document (same checksum)."""

    def __init__(self, existing_id: int | None = None) -> None:
        self.existing_id = existing_id
        msg = "A document with the same content has already been uploaded."
        if existing_id:
            msg += f" Existing document ID: {existing_id}."
        super().__init__(msg)


class ImportFailedError(DocumentError):
    """Financial record import from extraction failed."""
    pass
