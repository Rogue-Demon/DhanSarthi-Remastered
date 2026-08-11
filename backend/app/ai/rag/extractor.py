"""
Document text extractor abstraction for DhanSarthi RAG ingestion.
"""

from __future__ import annotations

import os
from app.ai.exceptions import AIAdvisorError


class DocumentExtractionError(AIAdvisorError):
    """Raised when text extraction from a file fails or produces empty content."""
    pass


class DocumentTextExtractor:
    """Extracts raw text content from Markdown, TXT, HTML, and document files."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm", ".json"}

    def extract_from_text(self, text: str) -> str:
        """Extract and validate text content supplied directly as string."""
        if not text or not text.strip():
            raise DocumentExtractionError("Extracted document content is empty or contains only whitespace.")
        return text.strip()

    def extract_from_file(self, file_path: str) -> str:
        """
        Extract text from local file path.

        Args:
            file_path: Path to the target document.

        Returns:
            str: Extracted raw text.

        Raises:
            DocumentExtractionError: If file is missing, empty, or unsupported format.
        """
        if not os.path.exists(file_path):
            raise DocumentExtractionError(f"File not found: '{file_path}'")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise DocumentExtractionError(
                f"Unsupported document format '{ext}'. Supported formats: {sorted(self.SUPPORTED_EXTENSIONS)}"
            )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if not content or not content.strip():
                raise DocumentExtractionError(f"Document '{file_path}' is empty or contains no readable text.")

            return content.strip()

        except Exception as exc:
            if isinstance(exc, DocumentExtractionError):
                raise
            raise DocumentExtractionError(f"Failed to read file '{file_path}': {str(exc)}") from exc
