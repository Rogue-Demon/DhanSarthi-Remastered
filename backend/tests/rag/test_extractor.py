"""
Unit tests for DocumentTextExtractor & TextCleaner — Phase 10.
"""

from __future__ import annotations

import tempfile
import pytest
from app.ai.rag.cleaner import TextCleaner
from app.ai.rag.extractor import DocumentExtractionError, DocumentTextExtractor


class TestDocumentTextExtractor:
    def test_extract_from_text_valid(self):
        ext = DocumentTextExtractor()
        res = ext.extract_from_text("  Valid document text  ")
        assert res == "Valid document text"

    def test_extract_from_text_empty_raises_error(self):
        ext = DocumentTextExtractor()
        with pytest.raises(DocumentExtractionError):
            ext.extract_from_text("   \n\t ")

    def test_extract_from_file_valid_txt(self):
        ext = DocumentTextExtractor()
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write("Sample file text content for RAG testing.")
            tmp_path = tmp.name

        res = ext.extract_from_file(tmp_path)
        assert "Sample file text" in res

    def test_extract_from_missing_file_raises_error(self):
        ext = DocumentTextExtractor()
        with pytest.raises(DocumentExtractionError) as exc:
            ext.extract_from_file("non_existent_file_999.txt")
        assert "File not found" in str(exc.value)

    def test_extract_from_unsupported_file_extension(self):
        ext = DocumentTextExtractor()
        with tempfile.NamedTemporaryFile("w", suffix=".exe", delete=False) as tmp:
            tmp.write("content")
            tmp_path = tmp.name

        with pytest.raises(DocumentExtractionError) as exc:
            ext.extract_from_file(tmp_path)
        assert "Unsupported document format" in str(exc.value)


class TestTextCleaner:
    def test_clean_normalizes_whitespace_and_newlines(self):
        cleaner = TextCleaner()
        raw = "Line 1   with   spaces\r\n\r\n\r\n\r\nLine 2"
        res = cleaner.clean(raw)
        assert res == "Line 1 with spaces\n\nLine 2"

    def test_clean_strips_control_chars(self):
        cleaner = TextCleaner()
        raw = "Text\x00with\x07null"
        res = cleaner.clean(raw)
        assert res == "Textwithnull"
