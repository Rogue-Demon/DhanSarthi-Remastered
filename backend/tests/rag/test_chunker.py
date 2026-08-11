"""
Unit tests for DeterministicChunker — Phase 10.
"""

from __future__ import annotations

import pytest
from app.ai.rag.chunker import DeterministicChunker


class TestDeterministicChunker:
    def test_empty_text_returns_empty_list(self):
        chunker = DeterministicChunker(chunk_size=300, chunk_overlap=30)
        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   \n\n  ") == []

    def test_small_document_single_chunk(self):
        chunker = DeterministicChunker(chunk_size=500, chunk_overlap=50)
        text = "This is a short financial guidance document about Systematic Investment Plans."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert "Systematic Investment Plans" in chunks[0].content

    def test_paragraph_split_boundaries(self):
        chunker = DeterministicChunker(chunk_size=150, chunk_overlap=0)
        text = (
            "Paragraph one is about tax-saving opportunities under Section 80C.\n\n"
            "Paragraph two discusses National Pension System contributions and retirement planning.\n\n"
            "Paragraph three covers fixed deposits and recurring deposits."
        )
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 2
        assert "Section 80C" in chunks[0].content

    def test_heading_preservation_in_metadata(self):
        chunker = DeterministicChunker(chunk_size=200, chunk_overlap=0)
        text = (
            "# Income Tax Guidelines\n\n"
            "This section covers tax slabs.\n\n"
            "## Deductions\n\n"
            "Section 80C offers deductions up to 1.5 lakh."
        )
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1
        sections = [c.metadata.get("section") for c in chunks]
        assert "Income Tax Guidelines" in sections or "Deductions" in sections

    def test_overlap_applied_to_subsequent_chunks(self):
        chunker = DeterministicChunker(chunk_size=100, chunk_overlap=20)
        text = (
            "First long block of text describing personal loan eligibility requirements and interest rates.\n\n"
            "Second long block of text detailing reducing balance EMI calculation methods and tenure limits."
        )
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Overlap prefix indicator '...' present on 2nd chunk
            assert chunks[1].content.startswith("...")
