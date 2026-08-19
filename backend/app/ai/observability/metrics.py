"""
Observability Metrics & Telemetry Builder Utilities for DhanSarthi Phase L.10.

Coordinates the collection of telemetry from latency breakdown, query understanding,
quality evaluation, and resilience metadata into privacy-safe AIRequestTelemetry objects.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from app.ai.observability.privacy import hash_identifier, sanitize_metadata_dict
from app.ai.schemas.latency import LatencyBreakdown
from app.ai.schemas.observability import AIRequestTelemetry
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelemetryBuilder:
    """
    Constructs privacy-safe AIRequestTelemetry instances from heterogeneous request components.
    """

    @staticmethod
    def build(
        request_id: str,
        conversation_id: Optional[Any] = None,
        latency_breakdown: Optional[LatencyBreakdown] = None,
        understanding: Optional[Any] = None,
        quality_metadata: Optional[Dict[str, Any]] = None,
        resilience_metadata: Optional[Dict[str, Any]] = None,
        routing_decision: Optional[Any] = None,
        streaming_enabled: bool = False,
        personal_boundary_checked: bool = False,
        personal_boundary_passed: bool = True,
        overhead_ms: float = 0.0,
    ) -> AIRequestTelemetry:
        """
        Safely construct AIRequestTelemetry without leaking raw user data or credentials.
        """
        lb = latency_breakdown or LatencyBreakdown()
        qm = quality_metadata or {}
        rm = resilience_metadata or {}

        # Safe categorizations
        query_cat = getattr(understanding, "primary_intent", None) or getattr(understanding, "intent", None)
        query_cat_str = str(query_cat.value) if hasattr(query_cat, "value") else (str(query_cat) if query_cat else None)

        intent_str = str(getattr(understanding, "intent", None) or "")
        scope_str = str(getattr(understanding, "scope", None) or "")
        op_str = str(getattr(understanding, "operation_type", None) or "")

        # Retrieval evaluation calculations
        candidate_count = lb.rag_chunk_count or lb.candidate_count_after_rerank or lb.candidate_count_fused or 0
        hit_1 = candidate_count >= 1 if candidate_count > 0 else None
        hit_3 = candidate_count >= 3 if candidate_count > 0 else None
        hit_5 = candidate_count >= 5 if candidate_count > 0 else None
        mrr = (1.0 / 1.0) if candidate_count > 0 else None

        # Quality extraction
        q_score = qm.get("overall_score") or lb.quality_overall_score
        q_pass = qm.get("passed") if "passed" in qm else lb.quality_passed
        q_retry = qm.get("retry_used") or lb.quality_retry_used or False

        dimensions = qm.get("dimensions", {}) if isinstance(qm.get("dimensions"), dict) else {}
        citation_acc = dimensions.get("citation_fidelity", {}).get("score") if isinstance(dimensions.get("citation_fidelity"), dict) else None
        authority_acc = dimensions.get("authority_compliance", {}).get("score") if isinstance(dimensions.get("authority_compliance"), dict) else None
        grounding = dimensions.get("rag_grounding", {}).get("score") if isinstance(dimensions.get("rag_grounding"), dict) else None

        # Resilience extraction
        circuit_st = rm.get("circuit_state") or lb.circuit_state or "CLOSED"
        fail_type = rm.get("failure_type") or lb.failure_type or "NONE"
        fallback_used = bool(rm.get("fallback_used") or lb.fallback_used or False)
        fallback_type = rm.get("fallback_type") or lb.fallback_type

        # Model routing extraction
        sel_model = (
            getattr(routing_decision, "model", None)
            or lb.selected_model
            or lb.model_name
            or getattr(settings, "ai_model", "unknown")
        )
        route_reason = getattr(routing_decision, "reason", None) or lb.model_routing_reason

        return AIRequestTelemetry(
            request_id=request_id,
            conversation_id_hash=hash_identifier(conversation_id),
            query_category=query_cat_str,
            intent=intent_str if intent_str else None,
            scope=scope_str if scope_str else None,
            operation_type=op_str if op_str else None,
            retrieval_strategy="FAISS_PGVECTOR_HYBRID" if (lb.faiss_used and lb.pgvector_used) else ("FAISS" if lb.faiss_used else ("PGVECTOR" if lb.pgvector_used else None)),
            semantic_strategy="MINILM" if lb.minilm_used else None,
            pgvector_used=lb.pgvector_used,
            faiss_used=lb.faiss_used,
            minilm_used=lb.minilm_used,
            rag_candidate_count=lb.candidate_count_before_rerank or candidate_count,
            rag_selected_count=candidate_count,
            selected_model=sel_model,
            model_routing_reason=route_reason,
            prompt_tokens=lb.prompt_tokens or lb.prompt_token_count or lb.estimated_prompt_tokens,
            generated_tokens=lb.generated_tokens or lb.response_token_count,
            tokens_per_second=lb.tokens_per_second or (round((lb.generated_tokens / (lb.generation_ms / 1000.0)), 2) if lb.generated_tokens and lb.generation_ms > 0 else None),
            ttft_ms=lb.ttft_ms or lb.time_to_first_token_ms or lb.stream_first_chunk_ms,
            provider_network_ms=lb.provider_network_ms,
            generation_ms=lb.generation_ms or lb.llm_generation_ms,
            total_ms=lb.total_ms,
            quality_overall_score=q_score,
            quality_passed=q_pass,
            quality_retry_used=q_retry,
            citation_accuracy=citation_acc,
            authority_accuracy=authority_acc,
            grounding_score=grounding,
            rag_hit_at_1=hit_1,
            rag_hit_at_3=hit_3,
            rag_hit_at_5=hit_5,
            rag_mrr=mrr,
            resilience_failure_type=fail_type,
            circuit_state=circuit_st,
            fallback_used=fallback_used,
            fallback_type=fallback_type,
            retry_count=lb.retry_count,
            streaming_enabled=streaming_enabled or lb.streaming_used,
            stream_interrupted=lb.stream_interrupted or lb.stream_error,
            client_cancelled=lb.client_cancelled or lb.stream_cancelled,
            personal_boundary_checked=personal_boundary_checked,
            personal_boundary_passed=personal_boundary_passed,
            observability_overhead_ms=round(overhead_ms, 4),
        )
