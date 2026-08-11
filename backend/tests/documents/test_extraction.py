"""
Tests for text and table extraction from PDF, CSV, and TXT files, and OCR-required flags.
"""

from __future__ import annotations

from app.documents.extraction.pdf_extractor import PDFDocumentExtractor
from app.documents.extraction.csv_extractor import CSVDocumentExtractor
from app.documents.extraction.text_extractor import TextDocumentExtractor
from app.documents.extraction.image_extractor import ImageDocumentExtractor
from app.documents.exceptions import ExtractionFailedError
import pytest


class TestDocumentTextExtraction:
    def test_text_file_extractor(self):
        extractor = TextDocumentExtractor()
        text_data = b"Line 1 text contents\nLine 2 text contents"
        out = extractor.extract(text_data)

        assert out.page_count == 1
        assert "Line 1" in out.raw_text
        assert not out.ocr_required

    def test_empty_text_file_raises_extraction_error(self):
        extractor = TextDocumentExtractor()
        with pytest.raises(ExtractionFailedError):
            extractor.extract(b"  \n  ")

    def test_csv_file_extractor_parses_tables(self):
        extractor = CSVDocumentExtractor()
        csv_data = b"Date,Description,Amount\n12-08-2026,Salary,50000\n13-08-2026,Rent,-15000"
        out = extractor.extract(csv_data)

        assert out.page_count == 1
        assert "Salary" in out.raw_text
        assert len(out.pages[0].tables) == 1
        table = out.pages[0].tables[0]
        assert len(table) == 3  # Header + 2 data rows
        assert table[0] == ["Date", "Description", "Amount"]
        assert table[1] == ["12-08-2026", "Salary", "50000"]
        assert not out.ocr_required

    def test_empty_csv_raises_extraction_error(self):
        extractor = CSVDocumentExtractor()
        with pytest.raises(ExtractionFailedError):
            extractor.extract(b"")

    def test_pdf_extractor_scanned_detects_ocr_required(self, monkeypatch):
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   "  # Empty / whitespace only
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        
        monkeypatch.setattr("app.documents.extraction.pdf_extractor.PdfReader", MagicMock(return_value=mock_reader))

        extractor = PDFDocumentExtractor()
        out = extractor.extract(b"dummy bytes")
        
        assert out.page_count == 1
        assert out.ocr_required

    def test_pdf_extractor_valid_text(self, monkeypatch):
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Some extracted financial text content."
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        
        monkeypatch.setattr("app.documents.extraction.pdf_extractor.PdfReader", MagicMock(return_value=mock_reader))

        extractor = PDFDocumentExtractor()
        out = extractor.extract(b"dummy bytes")
        
        assert out.page_count == 1
        assert not out.ocr_required
        assert "financial text" in out.raw_text

    def test_image_extractor_always_flags_ocr_required(self):
        extractor = ImageDocumentExtractor()
        out = extractor.extract(b"dummy image bytes")
        
        assert out.ocr_required
        assert out.raw_text == ""
