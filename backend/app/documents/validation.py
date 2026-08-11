"""
File validation for document uploads.

Validates size, extension, MIME type via magic bytes, filename safety,
and computes SHA-256 checksum.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import PurePosixPath
from typing import Optional

from app.core.config import settings
from app.documents.exceptions import (
    FileTooLargeError,
    InvalidDocumentError,
    UnsupportedFileTypeError,
)

# Allowed extensions → expected MIME types
ALLOWED_EXTENSIONS: dict[str, list[str]] = {
    ".pdf": ["application/pdf"],
    ".png": ["image/png"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".csv": ["text/csv", "application/csv", "text/plain"],
    ".txt": ["text/plain"],
}

# Magic byte signatures for content-type verification
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF"],
    "image/png": [b"\x89PNG"],
    "image/jpeg": [b"\xff\xd8\xff"],
}

_SAFE_FILENAME_PATTERN = re.compile(r"[^\w\.\-]")


class FileValidator:
    """Validates uploaded files before storage and processing."""

    @staticmethod
    def validate_size(data: bytes) -> None:
        """Reject files exceeding MAX_DOCUMENT_SIZE_MB."""
        max_bytes = settings.max_document_size_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise FileTooLargeError(
                size_mb=len(data) / (1024 * 1024),
                max_mb=settings.max_document_size_mb,
            )
        if len(data) == 0:
            raise InvalidDocumentError("File is empty.")

    @staticmethod
    def validate_extension(filename: str) -> str:
        """Validate file extension is in the allowlist. Returns the extension."""
        ext = PurePosixPath(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(ext or "no extension")
        return ext

    @staticmethod
    def validate_mime_type(filename: str, content_type: Optional[str]) -> str:
        """Validate MIME type against extension. Returns the validated MIME type."""
        ext = PurePosixPath(filename).suffix.lower()
        allowed_mimes = ALLOWED_EXTENSIONS.get(ext, [])
        if content_type and content_type in allowed_mimes:
            return content_type
        # Return the first allowed MIME for this extension
        if allowed_mimes:
            return allowed_mimes[0]
        raise UnsupportedFileTypeError(content_type or "unknown")

    @staticmethod
    def validate_magic_bytes(data: bytes, mime_type: str) -> None:
        """Verify file content matches expected magic bytes where known."""
        signatures = MAGIC_SIGNATURES.get(mime_type)
        if signatures is None:
            return  # No known signature for this type (CSV, TXT) — skip
        for sig in signatures:
            if data[:len(sig)] == sig:
                return
        raise InvalidDocumentError(
            f"File content does not match expected format for {mime_type}."
        )

    @staticmethod
    def compute_checksum(data: bytes) -> str:
        """Compute SHA-256 hex digest."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sanitize_filename(original: str) -> str:
        """Strip path traversal and dangerous characters from the filename."""
        # Extract only the basename
        name = PurePosixPath(original).name
        # Remove any remaining path separators
        name = name.replace("\\", "").replace("/", "")
        # Replace special chars
        name = _SAFE_FILENAME_PATTERN.sub("_", name)
        return name[:200] if name else "unnamed"

    @staticmethod
    def generate_storage_key(user_id: int, extension: str) -> str:
        """Generate a UUID-based storage key. Never uses the original filename."""
        file_uuid = uuid.uuid4().hex
        return f"{user_id}/{file_uuid}{extension}"

    @classmethod
    def validate_upload(
        cls,
        filename: str,
        content_type: Optional[str],
        data: bytes,
    ) -> dict:
        """Run all validations and return a result dict.

        Returns:
            dict with keys: extension, mime_type, checksum, sanitized_filename, file_size
        """
        cls.validate_size(data)
        ext = cls.validate_extension(filename)
        mime = cls.validate_mime_type(filename, content_type)
        cls.validate_magic_bytes(data, mime)
        checksum = cls.compute_checksum(data)
        safe_name = cls.sanitize_filename(filename)

        return {
            "extension": ext,
            "mime_type": mime,
            "checksum": checksum,
            "sanitized_filename": safe_name,
            "file_size": len(data),
        }
