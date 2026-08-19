"""
RAG Graceful Degradation and Failure Recovery Coordinator for Phase L.9.9.

Ensures that failures in vector indexing (FAISS), database querying (pgvector),
or semantic reranking (MiniLM) degrade gracefully rather than aborting the chat pipeline.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from app.ai.router import QueryIntent
from app.ai.schemas.advisor import RetrievedDocument
from app.ai.schemas.resilience import FallbackType, ResilienceFailureType
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGDegradationCoordinator:
    """
    Coordinates RAG component failures and ensures graceful fallback.
    
    Fallback Hierarchy:
      FAISS + pgvector -> pgvector only -> FAISS only -> Empty RAG set
    """

    def __init__(self) -> None:
        self.enabled = getattr(settings, "ai_rag_degradation_enabled", True)

    def handle_faiss_failure(self, error: Exception) -> FallbackType:
        """Log FAISS failure and flag PGVECTOR fallback."""
        logger.warning(f"RAG Degradation: FAISS vector index failed ({error}). Falling back to pgvector.")
        return FallbackType.PGVECTOR_FALLBACK

    def handle_pgvector_failure(self, error: Exception) -> FallbackType:
        """Log pgvector database failure and flag FAISS fallback."""
        logger.warning(f"RAG Degradation: pgvector query failed ({error}). Falling back to FAISS index.")
        return FallbackType.DETERMINISTIC_FALLBACK

    def handle_minilm_failure(self, error: Exception) -> None:
        """Log MiniLM failure without interrupting retrieval pipeline."""
        logger.warning(f"RAG Degradation: MiniLM semantic scoring failed ({error}). Continuing with standard ranking.")

    def should_require_authoritative_grounding(
        self, intent: QueryIntent, retrieved_docs: List[RetrievedDocument], is_regulatory: bool = False
    ) -> bool:
        """
        Determine if query demands authoritative documents and cannot be safely answered with 0 chunks.
        """
        if is_regulatory and len(retrieved_docs) == 0:
            return True
        return False
