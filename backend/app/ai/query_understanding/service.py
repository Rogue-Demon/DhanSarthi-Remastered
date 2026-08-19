"""
Query Understanding Service for DhanSarthi.

Orchestrates query normalization, typo correction, Hinglish parsing,
conversation reference resolution, entity extraction, intent integration,
scope detection, and retrieval query construction.
"""

from __future__ import annotations

import re
import time
from typing import Any, List, Optional

from app.ai.query_understanding.entity_extractor import EntityExtractor
from app.ai.query_understanding.hinglish_parser import HinglishParser
from app.ai.query_understanding.intent_scope_classifier import IntentScopeClassifier
from app.ai.query_understanding.reference_resolver import ReferenceResolver
from app.ai.query_understanding.retrieval_rewriter import RetrievalQueryRewriter
from app.ai.query_understanding.typo_normalizer import TypoNormalizer
from app.ai.router import IntentRouter, QueryIntent, SubIntent
from app.ai.schemas.query_understanding import (
    ConfidenceScores,
    ConversationReference,
    QueryUnderstanding,
)


class QueryUnderstandingService:
    """Lightweight, deterministic Query Understanding Layer."""

    def __init__(self) -> None:
        self._typo = TypoNormalizer()
        self._hinglish = HinglishParser()
        self._resolver = ReferenceResolver()
        self._extractor = EntityExtractor()
        self._router = IntentRouter()
        self._classifier = IntentScopeClassifier()
        self._rewriter = RetrievalQueryRewriter()

    def analyze(
        self,
        query: str,
        history: Optional[List] = None,
        tracker: Optional[Any] = None,
    ) -> QueryUnderstanding:
        """
        Analyze incoming query and produce structured QueryUnderstanding.

        Args:
            query: Raw user message string.
            history: Optional recent conversation history messages.
            tracker: Optional LatencyTracker instance for profiling.

        Returns:
            QueryUnderstanding: Structured query understanding payload.
        """
        start_qu = time.perf_counter() if tracker else 0.0

        if not query or not query.strip():
            qu = QueryUnderstanding(
                original_query="",
                normalized_query="",
                corrected_query="",
                resolved_query="",
                retrieval_query="",
                intent=QueryIntent.CASUAL,
                sub_intent=SubIntent.GENERAL,
            )
            if tracker and start_qu > 0.0:
                tracker.record("query_understanding_ms", (time.perf_counter() - start_qu) * 1000.0)
            return qu

        original_query = query
        raw_trimmed = query.strip()

        # 1. Base Normalization
        norm_text = self._base_normalize(raw_trimmed)

        # 2. Financial Typo Normalization
        t0 = time.perf_counter() if tracker else 0.0
        corrected_text, correction_applied, typo_conf = self._typo.correct(norm_text)
        if tracker and t0 > 0.0:
            tracker.record("typo_normalization_ms", (time.perf_counter() - t0) * 1000.0)

        # 3. Hinglish & Mixed-Language Understanding
        t0 = time.perf_counter() if tracker else 0.0
        translated_text, is_hinglish, lang_code = self._hinglish.parse(corrected_text)
        if tracker and t0 > 0.0:
            tracker.record("hinglish_ms", (time.perf_counter() - t0) * 1000.0)

        # 4. Conversation Reference Resolution (Pronoun replacement)
        t0 = time.perf_counter() if tracker else 0.0
        resolved_text, conv_ref = self._resolver.resolve(translated_text, history)
        if tracker and t0 > 0.0:
            tracker.record("reference_resolution_ms", (time.perf_counter() - t0) * 1000.0)

        # 5. Entity & Temporal Extraction
        t0 = time.perf_counter() if tracker else 0.0
        entities, temporal_refs = self._extractor.extract(resolved_text)
        financial_terms = [e.value for e in entities if e.value]
        if tracker and t0 > 0.0:
            tracker.record("entity_extraction_ms", (time.perf_counter() - t0) * 1000.0)

        # 6 & 7. Intent & Sub-Intent Classification + QueryExecutionPlan
        t0 = time.perf_counter() if tracker else 0.0
        intent = self._router.classify(resolved_text)
        sub_intent = self._router.classify_sub_intent(resolved_text)
        execution_plan = self._classifier.build_execution_plan(
            query=original_query,
            resolved_query=resolved_text,
            intent=intent,
            sub_intent=sub_intent,
            entities=entities,
            conv_reference=conv_ref,
            history=history,
        )
        if tracker and t0 > 0.0:
            tracker.record("intent_scope_ms", (time.perf_counter() - t0) * 1000.0)

        requires_personal_data = execution_plan.requires_financial_engine
        requires_rag = execution_plan.requires_rag
        requires_market_data = execution_plan.requires_market_data
        requires_conv_ctx = execution_plan.requires_conversation_context

        partial_understanding = QueryUnderstanding(
            original_query=original_query,
            normalized_query=norm_text,
            corrected_query=corrected_text,
            resolved_query=resolved_text,
            retrieval_query=resolved_text,
            language=lang_code,
            detected_language_mix=is_hinglish,
            intent=intent,
            sub_intent=sub_intent,
            entities=entities,
            financial_terms=financial_terms,
            temporal_references=temporal_refs,
            conversation_reference=conv_ref,
            requires_personal_data=requires_personal_data,
            requires_rag=requires_rag,
            requires_market_data=requires_market_data,
            requires_conversation_context=requires_conv_ctx,
            execution_plan=execution_plan,
            correction_applied=correction_applied,
            hinglish_translated=is_hinglish,
        )

        # 8. Phase L.3 Intelligent Retrieval Query Rewriting
        t0 = time.perf_counter() if tracker else 0.0
        rewrite_result = self._rewriter.rewrite(partial_understanding, execution_plan)
        retrieval_query = rewrite_result.retrieval_query
        if tracker and t0 > 0.0:
            tracker.record("retrieval_rewrite_ms", (time.perf_counter() - t0) * 1000.0)

        conf = ConfidenceScores(
            spelling_correction=typo_conf,
            reference_resolution=conv_ref.confidence if conv_ref else None,
            intent_classification=execution_plan.confidence,
            entity_extraction=1.0,
        )

        partial_understanding.retrieval_query = retrieval_query
        partial_understanding.confidence = conf

        if tracker and start_qu > 0.0:
            tracker.record("query_understanding_ms", (time.perf_counter() - start_qu) * 1000.0)

        return partial_understanding

    def _base_normalize(self, text: str) -> str:
        """Collapse whitespace and normalize harmless repeated characters."""
        clean = re.sub(r"\s+", " ", text).strip()
        # Lowercase for canonical string except uppercase acronyms
        return clean

    def _construct_retrieval_query(
        self,
        resolved_text: str,
        financial_terms: List[str],
        intent: QueryIntent,
        temporal_refs: List,
    ) -> str:
        """
        Construct a retrieval-optimized search string.

        Appends canonical concept keywords for vector search without modifying
        the prompt presented to the user/LLM.
        """
        if intent == QueryIntent.CASUAL:
            return resolved_text

        parts = [resolved_text]
        for term in financial_terms:
            if term.lower() not in resolved_text.lower():
                parts.append(term)

        # Append historical markers if historical intent detected
        for t_ref in temporal_refs:
            if t_ref.is_historical and "historical" not in resolved_text.lower():
                parts.append("historical rules regulations")

        return " ".join(parts)
