"""
Adaptive Retrieval Router for DhanSarthi Phase L.6.

Provides deterministic, rules-based strategy selection and candidate bound tuning
before executing database and FAISS retrieval pipelines.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional

from app.ai.router import QueryIntent
from app.ai.schemas.query_execution_plan import OperationType, QueryExecutionPlan, QueryScope
from app.ai.schemas.query_understanding import QueryUnderstanding
from app.ai.schemas.retrieval_strategy import (
    RetrievalExecutionPlan,
    RetrievalStrategy,
    SemanticStrategy,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.query_understanding.intent_scope_classifier import IntentScopeClassifier


class AdaptiveRetrievalRouter:
    """
    Lightweight, deterministic router that selects retrieval strategies,
    candidate bounds, RRF parameters, and semantic model execution flags.
    """

    def __init__(
        self,
        query_understanding_service: Optional[QueryUnderstandingService] = None,
        intent_scope_classifier: Optional[IntentScopeClassifier] = None,
    ) -> None:
        self._understanding = query_understanding_service or QueryUnderstandingService()
        self._classifier = intent_scope_classifier or IntentScopeClassifier()

    AUTHORITY_KEYWORDS = {
        "rbi", "reserve bank", "sebi", "income tax", "pfrda", "amfi", "tax", "itr",
        "80c", "80d", "tds", "stcg", "ltcg", "regulation", "policy", "rule", "circular",
        "guideline", "master direction", "dicgc", "riskometer"
    }

    HISTORICAL_PATTERNS = [
        r"\bfy\s*\d{2,4}[-\s]?\d{2,4}\b",
        r"\bay\s*\d{2,4}[-\s]?\d{2,4}\b",
        r"\bold\b",
        r"\bprevious\b",
        r"\bformer\b",
        r"\bhistorical\b",
        r"\bpast\b",
        r"\b2019\b",
        r"\b2020\b",
        r"\b2021\b",
        r"\b2022\b",
        r"\b2023\b",
        r"\b2024\b",
    ]
    HISTORICAL_REGEX = re.compile("|".join(HISTORICAL_PATTERNS), re.IGNORECASE)

    def route(
        self,
        query_understanding: Optional[QueryUnderstanding] = None,
        execution_plan: Optional[QueryExecutionPlan] = None,
        retrieval_query: str = "",
        tracker: Optional[Any] = None,
    ) -> RetrievalExecutionPlan:
        """
        Deterministically compute a RetrievalExecutionPlan for the input query.

        Args:
            query_understanding: Output payload from Phase L.1 Query Understanding.
            execution_plan: Output payload from Phase L.2 Intent & Scope Classifier.
            retrieval_query: Final expanded/rewritten query string from Phase L.3.
            tracker: Optional LatencyTracker instance for profiling.

        Returns:
            RetrievalExecutionPlan: Selected retrieval strategy, top-k, RRF, and MiniLM settings.
        """
        start_t = time.perf_counter() if tracker else 0.0
        plan = self._route_internal(query_understanding, execution_plan, retrieval_query)
        if tracker and start_t > 0.0:
            tracker.record("adaptive_routing_ms", (time.perf_counter() - start_t) * 1000.0)
        return plan

    def _route_internal(
        self,
        query_understanding: Optional[QueryUnderstanding],
        execution_plan: Optional[QueryExecutionPlan],
        retrieval_query: str,
    ) -> RetrievalExecutionPlan:
        if query_understanding is None and execution_plan is None and retrieval_query:
            try:
                query_understanding = self._understanding.analyze(retrieval_query)
            except Exception:
                pass

        if execution_plan is None and query_understanding:
            try:
                execution_plan = self._classifier.build_execution_plan(
                    query=query_understanding.original_query,
                    resolved_query=query_understanding.resolved_query,
                    intent=query_understanding.intent,
                    sub_intent=query_understanding.sub_intent,
                    entities=query_understanding.entities,
                )
            except Exception:
                pass

        # If adaptive retrieval is disabled in config, fallback to default HYBRID
        if not getattr(settings, "adaptive_retrieval_enabled", True):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=settings.adaptive_default_pgvector_k,
                faiss_top_k=settings.adaptive_default_faiss_k,
                use_rrf=True,
                use_minilm=True,
                rrf_k=settings.adaptive_rrf_k_default,
                reason="adaptive_disabled_fallback",
            )

        q_clean = (retrieval_query or "").strip().lower()

        # 1. CASUAL / META QUERY BYPASS
        if (
            (execution_plan and execution_plan.scope == QueryScope.CASUAL)
            or (execution_plan and execution_plan.intent == QueryIntent.CASUAL)
            or (query_understanding and query_understanding.intent == QueryIntent.CASUAL)
        ):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.NONE,
                semantic_strategy=SemanticStrategy.NONE,
                pgvector_top_k=0,
                faiss_top_k=0,
                use_rrf=False,
                use_minilm=False,
                reason="casual_query_bypass",
            )

        # 2. AMBIGUOUS / CLARIFICATION REQUIRED BYPASS
        if execution_plan and (execution_plan.clarification_required or execution_plan.scope == QueryScope.AMBIGUOUS):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.NONE,
                semantic_strategy=SemanticStrategy.NONE,
                pgvector_top_k=0,
                faiss_top_k=0,
                use_rrf=False,
                use_minilm=False,
                reason="ambiguous_clarification_required",
            )

        # 3. PERSONAL FINANCE / USER METRICS BYPASS (Financial Engine handles personal numbers)
        is_mixed_or_rag = (
            (execution_plan and execution_plan.requires_rag)
            or (execution_plan and execution_plan.scope in (QueryScope.MIXED, QueryScope.EDUCATIONAL, QueryScope.COMPARISON))
            or (query_understanding and query_understanding.intent in (QueryIntent.MIXED, QueryIntent.GENERAL_FINANCE))
            or (execution_plan and execution_plan.intent in (QueryIntent.MIXED, QueryIntent.GENERAL_FINANCE))
        )

        if execution_plan and (execution_plan.scope == QueryScope.PERSONAL_LOOKUP or execution_plan.intent == QueryIntent.PERSONAL_FINANCE) and not is_mixed_or_rag:
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.NONE,
                semantic_strategy=SemanticStrategy.NONE,
                pgvector_top_k=0,
                faiss_top_k=0,
                use_rrf=False,
                use_minilm=False,
                reason="personal_finance_engine_only",
            )

        if execution_plan and execution_plan.requires_financial_engine and not is_mixed_or_rag:
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.NONE,
                semantic_strategy=SemanticStrategy.NONE,
                pgvector_top_k=0,
                faiss_top_k=0,
                use_rrf=False,
                use_minilm=False,
                reason="personal_finance_engine_only",
            )

        # 4. COMPARISON QUERIES
        if (
            (execution_plan and (execution_plan.scope == QueryScope.COMPARISON or execution_plan.operation == OperationType.COMPARE or execution_plan.comparison_info.is_comparison))
            or (" vs " in q_clean or " or " in q_clean or "compare" in q_clean or "difference between" in q_clean)
        ):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=getattr(settings, "adaptive_comparison_k", 25),
                faiss_top_k=getattr(settings, "adaptive_comparison_k", 25),
                use_rrf=True,
                use_minilm=True,
                rrf_k=getattr(settings, "adaptive_rrf_k_comparison", 40),
                reason="comparison_query",
            )

        # 5. AUTHORITY-SENSITIVE QUERIES (RBI, SEBI, Tax, PFRDA, AMFI)
        has_authority_kw = any(kw in q_clean for kw in self.AUTHORITY_KEYWORDS)
        if has_authority_kw:
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=getattr(settings, "adaptive_authority_k", 25),
                faiss_top_k=getattr(settings, "adaptive_authority_k", 25),
                use_rrf=True,
                use_minilm=True,
                rrf_k=getattr(settings, "adaptive_rrf_k_authority", 50),
                reason="authority_sensitive",
            )

        # 6. HISTORICAL QUERIES
        has_historical = bool(self.HISTORICAL_REGEX.search(q_clean))
        has_temporal = False
        if query_understanding and query_understanding.temporal_references:
            has_temporal = any(t.is_historical for t in query_understanding.temporal_references)

        if has_historical or has_temporal:
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=getattr(settings, "adaptive_historical_k", 25),
                faiss_top_k=getattr(settings, "adaptive_historical_k", 25),
                use_rrf=True,
                use_minilm=True,
                rrf_k=getattr(settings, "adaptive_rrf_k_default", 60),
                reason="historical_query",
            )

        # 7. SHORT FINANCIAL ENTITY QUERIES ("SIP?", "PPF?", "NAV?")
        if len(q_clean) <= 15 or len(q_clean.split()) <= 2:
            if (query_understanding and query_understanding.entities) or (execution_plan and execution_plan.entities):
                return RetrievalExecutionPlan(
                    strategy=RetrievalStrategy.HYBRID,
                    semantic_strategy=SemanticStrategy.MINILM,
                    pgvector_top_k=getattr(settings, "adaptive_definition_k", 15),
                    faiss_top_k=getattr(settings, "adaptive_definition_k", 15),
                    use_rrf=True,
                    use_minilm=True,
                    rrf_k=getattr(settings, "adaptive_rrf_k_default", 60),
                    reason="short_financial_entity",
                )

        # 8. SIMPLE DEFINITIONS / CONCEPT EXPLANATIONS
        if execution_plan and (execution_plan.scope == QueryScope.EDUCATIONAL or execution_plan.operation in (OperationType.DEFINE, OperationType.EXPLAIN)):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=getattr(settings, "adaptive_definition_k", 15),
                faiss_top_k=getattr(settings, "adaptive_definition_k", 15),
                use_rrf=True,
                use_minilm=True,
                rrf_k=getattr(settings, "adaptive_rrf_k_default", 60),
                reason="definition_concept",
            )

        # 9. MIXED QUERIES (Personal metrics + RAG guidance)
        if (execution_plan and execution_plan.scope == QueryScope.MIXED) or (query_understanding and query_understanding.intent == QueryIntent.MIXED):
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.HYBRID,
                semantic_strategy=SemanticStrategy.MINILM,
                pgvector_top_k=getattr(settings, "adaptive_default_pgvector_k", 20),
                faiss_top_k=getattr(settings, "adaptive_default_faiss_k", 20),
                use_rrf=True,
                use_minilm=True,
                rrf_k=getattr(settings, "adaptive_rrf_k_default", 60),
                reason="mixed_personal_and_general",
            )

        # 10. NON-RAG EXPLICIT CHECK
        if execution_plan and not execution_plan.requires_rag:
            return RetrievalExecutionPlan(
                strategy=RetrievalStrategy.NONE,
                semantic_strategy=SemanticStrategy.NONE,
                pgvector_top_k=0,
                faiss_top_k=0,
                use_rrf=False,
                use_minilm=False,
                reason="non_rag_query",
            )

        # 11. DEFAULT GENERAL FINANCIAL KNOWLEDGE ROUTE
        return RetrievalExecutionPlan(
            strategy=RetrievalStrategy.HYBRID,
            semantic_strategy=SemanticStrategy.MINILM,
            pgvector_top_k=getattr(settings, "adaptive_default_pgvector_k", 20),
            faiss_top_k=getattr(settings, "adaptive_default_faiss_k", 20),
            use_rrf=True,
            use_minilm=True,
            rrf_k=getattr(settings, "adaptive_rrf_k_default", 60),
            reason="general_financial_knowledge",
        )
