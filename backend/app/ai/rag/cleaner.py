"""
Text cleaner for RAG document normalization.
"""

from __future__ import annotations

import re


class TextCleaner:
    """Normalizes whitespace and formats raw text while preserving headings and lists."""

    def clean(self, raw_text: str) -> str:
        """
        Clean and normalize raw extracted text.

        Args:
            raw_text: Raw string extracted from document source.

        Returns:
            str: Cleaned and normalized text.
        """
        if not raw_text:
            return ""

        if isinstance(raw_text, list):
            raw_text = "\n\n".join(str(item) for item in raw_text)
        elif not isinstance(raw_text, str):
            raw_text = str(raw_text)

        # Replace NULL characters and control chars (except newline/tab)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", raw_text)

        # Normalize Windows CRLF line endings to LF
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace excessive spaces/tabs within lines while keeping newlines
        lines = []
        for line in text.split("\n"):
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(cleaned_line)

        text = "\n".join(lines)

        # Collapse 3 or more consecutive newlines to 2 newlines (paragraph boundary)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
