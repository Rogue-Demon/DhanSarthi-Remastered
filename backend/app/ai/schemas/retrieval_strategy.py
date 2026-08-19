"""
Retrieval Strategy & Execution Plan Schemas for DhanSarthi Phase L.6.

Defines retrieval strategy routing enums, semantic scoring strategy enums, and
deterministic retrieval execution plans.
"""

from __future__ import annotations

import enum
from pydantic import BaseModel, Field


class RetrievalStrategy(str, enum.Enum):
    """Primary retrieval strategy mode."""

    NONE = "NONE"
    PGVECTOR_ONLY = "PGVECTOR_ONLY"
    FAISS_ONLY = "FAISS_ONLY"
    HYBRID = "HYBRID"


class SemanticStrategy(str, enum.Enum):
    """Downstream candidate pool semantic scoring model strategy."""

    NONE = "NONE"
    MINILM = "MINILM"


class RetrievalExecutionPlan(BaseModel):
    """
    Deterministic execution plan for retrieval & fusion pipeline specifying
    which retrieval strategies, semantic models, top-k candidate bounds,
    RRF parameters, and fallback rules to apply.
    """

    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    semantic_strategy: SemanticStrategy = SemanticStrategy.MINILM

    pgvector_top_k: int = 20
    faiss_top_k: int = 20

    use_rrf: bool = True
    use_minilm: bool = True
    rrf_k: int = 60

    confidence: float = 1.0
    reason: str = "default_hybrid"

    fallback_allowed: bool = True
