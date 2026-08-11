"""
Deterministic chunker for RAG document chunking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TextChunk:
    """Represents an extracted chunk with metadata."""

    chunk_index: int
    content: str
    token_count: int
    metadata: Dict[str, str] = field(default_factory=dict)


class DeterministicChunker:
    """Paragraph and section-heading aware document chunker with configurable overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self.chunk_size = max(100, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size // 2))

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split document text into structured chunks based on paragraph and heading boundaries.

        Args:
            text: Cleaned text string.

        Returns:
            List[TextChunk]: Ordered list of chunk objects.
        """
        if not text or not text.strip():
            return []

        # Split into paragraph blocks
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        raw_chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            if current_length + para_len + 1 <= self.chunk_size:
                current_chunk.append(para)
                current_length += para_len + 1
            else:
                if current_chunk:
                    raw_chunks.append("\n\n".join(current_chunk))

                # Handle paragraphs that exceed chunk_size individually by sentence splitting
                if para_len > self.chunk_size:
                    sub_chunks = self._split_large_paragraph(para)
                    raw_chunks.extend(sub_chunks[:-1])
                    current_chunk = [sub_chunks[-1]] if sub_chunks else []
                    current_length = len(sub_chunks[-1]) if sub_chunks else 0
                else:
                    current_chunk = [para]
                    current_length = para_len

        if current_chunk:
            raw_chunks.append("\n\n".join(current_chunk))

        # Apply overlap between neighboring chunks if configured
        final_chunks: List[TextChunk] = []
        last_section = "General"

        for idx, content in enumerate(raw_chunks):
            # Detect Markdown section heading if present
            heading_match = re.search(r"^#{1,4}\s+(.+)$", content, re.MULTILINE)
            if heading_match:
                last_section = heading_match.group(1).strip()

            chunk_text_content = content
            if idx > 0 and self.chunk_overlap > 0:
                prev_text = raw_chunks[idx - 1]
                overlap_prefix = prev_text[-self.chunk_overlap:]
                chunk_text_content = f"...{overlap_prefix}\n\n{content}"

            # Approximate token count (words * 1.3)
            approx_tokens = int(len(chunk_text_content.split()) * 1.3)

            final_chunks.append(
                TextChunk(
                    chunk_index=idx,
                    content=chunk_text_content,
                    token_count=approx_tokens,
                    metadata={"section": last_section},
                )
            )

        return final_chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a long paragraph by sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks: List[str] = []
        current: List[str] = []
        length = 0

        for s in sentences:
            if length + len(s) + 1 <= self.chunk_size:
                current.append(s)
                length += len(s) + 1
            else:
                if current:
                    chunks.append(" ".join(current))
                current = [s]
                length = len(s)

        if current:
            chunks.append(" ".join(current))

        return chunks
