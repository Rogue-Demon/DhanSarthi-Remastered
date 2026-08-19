"""
Metrics Aggregation & Production AI Health Scorecard Evaluator for DhanSarthi Phase L.10.

Calculates SLA percentiles, RAG retrieval quality, model distributions, resilience rates,
and classifies system health (HEALTHY / DEGRADED / CRITICAL) against configurable thresholds.
"""

from __future__ import annotations

import collections
import logging
from typing import Dict, List, Optional

from app.ai.schemas.evaluation_metrics import PercentileDistribution, RAGEvaluationSummary
from app.ai.schemas.observability import (
    AIRequestTelemetry,
    BoundaryHealthSummary,
    HealthStatus,
    InferenceHealthSummary,
    LatencyHealthSummary,
    QualityHealthSummary,
    ResilienceHealthSummary,
    SystemHealthScorecard,
    SystemHealthSummary,
    TimeWindow,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """
    Aggregates list of AIRequestTelemetry records into structured summaries and evaluates health status.
    """

    def __init__(
        self,
        p95_latency_threshold: Optional[float] = None,
        min_quality_score: Optional[float] = None,
        min_citation_accuracy: Optional[float] = None,
        min_grounding_score: Optional[float] = None,
        max_fallback_rate: Optional[float] = None,
        max_retry_rate: Optional[float] = None,
        max_stream_interruption_rate: Optional[float] = None,
    ) -> None:
        self.p95_latency_threshold = p95_latency_threshold or getattr(settings, "ai_health_p95_latency_ms", 20000.0)
        self.min_quality_score = min_quality_score or getattr(settings, "ai_health_min_quality_score", 0.90)
        self.min_citation_accuracy = min_citation_accuracy or getattr(settings, "ai_health_min_citation_accuracy", 0.95)
        self.min_grounding_score = min_grounding_score or getattr(settings, "ai_health_min_grounding_score", 0.95)
        self.max_fallback_rate = max_fallback_rate or getattr(settings, "ai_health_max_fallback_rate", 0.10)
        self.max_retry_rate = max_retry_rate or getattr(settings, "ai_health_max_retry_rate", 0.20)
        self.max_stream_interruption_rate = max_stream_interruption_rate or getattr(settings, "ai_health_max_stream_interruption_rate", 0.05)

    def aggregate(
        self,
        telemetries: List[AIRequestTelemetry],
        time_window: TimeWindow = TimeWindow.RECENT,
    ) -> SystemHealthScorecard:
        """
        Produce a full SystemHealthScorecard from a list of telemetry records.
        """
        n = len(telemetries)
        if n == 0:
            return SystemHealthScorecard(
                status=HealthStatus.HEALTHY,
                time_window=time_window,
                sample_count=0,
                status_reasons=["No telemetry records in selected window."],
            )

        # 1. System Health
        failed_requests = sum(1 for t in telemetries if t.resilience_failure_type not in (None, "NONE") and not t.fallback_used and not t.personal_boundary_passed)
        successful_requests = n - failed_requests
        success_rate = round(successful_requests / n, 4) if n > 0 else 1.0

        system_summary = SystemHealthSummary(
            total_requests=n,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
        )

        # 2. Latency Health
        total_latencies = [t.total_ms for t in telemetries if t.total_ms is not None and t.total_ms > 0]
        ttft_latencies = [t.ttft_ms for t in telemetries if t.ttft_ms is not None and t.ttft_ms > 0]
        gen_latencies = [t.generation_ms for t in telemetries if t.generation_ms is not None and t.generation_ms > 0]
        net_latencies = [t.provider_network_ms for t in telemetries if t.provider_network_ms is not None and t.provider_network_ms > 0]

        latency_summary = LatencyHealthSummary(
            total_latency=PercentileDistribution.from_values(total_latencies),
            ttft_latency=PercentileDistribution.from_values(ttft_latencies),
            generation_latency=PercentileDistribution.from_values(gen_latencies),
            provider_network_latency=PercentileDistribution.from_values(net_latencies),
        )

        # 3. Inference Health
        tps_vals = [t.tokens_per_second for t in telemetries if t.tokens_per_second is not None and t.tokens_per_second > 0]
        prompt_toks = [t.prompt_tokens for t in telemetries if t.prompt_tokens is not None]
        gen_toks = [t.generated_tokens for t in telemetries if t.generated_tokens is not None]

        models_counter: Dict[str, int] = collections.defaultdict(int)
        routing_reasons_counter: Dict[str, int] = collections.defaultdict(int)
        for t in telemetries:
            if t.selected_model:
                models_counter[t.selected_model] += 1
            if t.model_routing_reason:
                routing_reasons_counter[t.model_routing_reason] += 1

        inference_summary = InferenceHealthSummary(
            avg_tokens_per_second=round(sum(tps_vals) / len(tps_vals), 2) if tps_vals else 0.0,
            avg_prompt_tokens=round(sum(prompt_toks) / len(prompt_toks), 1) if prompt_toks else 0.0,
            avg_generated_tokens=round(sum(gen_toks) / len(gen_toks), 1) if gen_toks else 0.0,
            model_distribution=dict(models_counter),
            routing_reason_distribution=dict(routing_reasons_counter),
        )

        # 4. RAG Health
        rag_records = [t for t in telemetries if (t.rag_selected_count > 0 or t.pgvector_used or t.faiss_used)]
        rag_count = len(rag_records)

        hit1_count = sum(1 for t in rag_records if t.rag_hit_at_1 is True)
        hit3_count = sum(1 for t in rag_records if t.rag_hit_at_3 is True)
        hit5_count = sum(1 for t in rag_records if t.rag_hit_at_5 is True)
        mrr_scores = [t.rag_mrr for t in rag_records if t.rag_mrr is not None]
        citations = [t.citation_accuracy for t in telemetries if t.citation_accuracy is not None]
        authorities = [t.authority_accuracy for t in telemetries if t.authority_accuracy is not None]
        groundings = [t.grounding_score for t in telemetries if t.grounding_score is not None]

        rag_summary = RAGEvaluationSummary(
            total_queries=rag_count,
            hit_at_1=round(hit1_count / rag_count, 4) if rag_count > 0 else 1.0,
            hit_at_3=round(hit3_count / rag_count, 4) if rag_count > 0 else 1.0,
            hit_at_5=round(hit5_count / rag_count, 4) if rag_count > 0 else 1.0,
            mrr=round(sum(mrr_scores) / len(mrr_scores), 4) if mrr_scores else 1.0,
            citation_accuracy=round(sum(citations) / len(citations), 4) if citations else 1.0,
            authority_accuracy=round(sum(authorities) / len(authorities), 4) if authorities else 1.0,
            grounding_score=round(sum(groundings) / len(groundings), 4) if groundings else 1.0,
        )

        # 5. Quality Health
        quality_evaluated = [t for t in telemetries if t.quality_passed is not None]
        q_count = len(quality_evaluated)
        q_passed = sum(1 for t in quality_evaluated if t.quality_passed is True)
        q_scores = [t.quality_overall_score for t in quality_evaluated if t.quality_overall_score is not None]
        retries = sum(1 for t in telemetries if t.quality_retry_used or t.retry_count > 0)
        fallbacks = sum(1 for t in telemetries if t.fallback_used)

        quality_summary = QualityHealthSummary(
            quality_pass_rate=round(q_passed / q_count, 4) if q_count > 0 else 1.0,
            avg_quality_score=round(sum(q_scores) / len(q_scores), 4) if q_scores else 1.0,
            retry_rate=round(retries / n, 4) if n > 0 else 0.0,
            fallback_rate=round(fallbacks / n, 4) if n > 0 else 0.0,
        )

        # 6. Resilience Health
        latest_circuit_state = telemetries[-1].circuit_state if telemetries else "CLOSED"
        circuit_trips = sum(1 for t in telemetries if t.circuit_state == "OPEN")
        provider_errs = sum(1 for t in telemetries if t.resilience_failure_type not in (None, "NONE"))
        model_fallbacks = sum(1 for t in telemetries if t.fallback_used and t.fallback_type in ("MODEL_FALLBACK", "model_fallback"))
        safe_fallbacks = sum(1 for t in telemetries if t.fallback_used and t.fallback_type in ("SAFE_FALLBACK", "safe_fallback"))
        stream_interrupts = sum(1 for t in telemetries if t.stream_interrupted)
        client_cancels = sum(1 for t in telemetries if t.client_cancelled)

        resilience_summary = ResilienceHealthSummary(
            circuit_breaker_state=latest_circuit_state,
            circuit_breaker_trips=circuit_trips,
            provider_failure_count=provider_errs,
            provider_failure_rate=round(provider_errs / n, 4) if n > 0 else 0.0,
            model_fallback_count=model_fallbacks,
            model_fallback_rate=round(model_fallbacks / n, 4) if n > 0 else 0.0,
            safe_fallback_count=safe_fallbacks,
            safe_fallback_rate=round(safe_fallbacks / n, 4) if n > 0 else 0.0,
            stream_interruption_count=stream_interrupts,
            stream_interruption_rate=round(stream_interrupts / n, 4) if n > 0 else 0.0,
            client_cancellation_count=client_cancels,
        )

        # 7. Boundary Health
        pf_checked = sum(1 for t in telemetries if t.personal_boundary_checked)
        pf_passed = sum(1 for t in telemetries if t.personal_boundary_checked and t.personal_boundary_passed)
        pf_failed = sum(1 for t in telemetries if t.personal_boundary_checked and not t.personal_boundary_passed)
        compliance_rate = round(pf_passed / pf_checked, 4) if pf_checked > 0 else 1.0

        boundary_summary = BoundaryHealthSummary(
            personal_boundary_checks=pf_checked,
            personal_boundary_passes=pf_passed,
            personal_boundary_failures=pf_failed,
            boundary_compliance_rate=compliance_rate,
            safety_validation_pass_rate=1.0,
        )

        # 8. Observability Overhead
        overheads = [t.observability_overhead_ms for t in telemetries if t.observability_overhead_ms > 0]
        avg_overhead = round(sum(overheads) / len(overheads), 4) if overheads else 0.0

        # 9. Health Status Classification
        status = HealthStatus.HEALTHY
        reasons: List[str] = []

        # CRITICAL conditions
        if pf_failed > 0:
            status = HealthStatus.CRITICAL
            reasons.append(f"CRITICAL: {pf_failed} personal finance boundary violation(s) detected (zero tolerance).")

        if latest_circuit_state == "OPEN":
            status = HealthStatus.CRITICAL
            reasons.append("CRITICAL: Circuit breaker is currently OPEN.")

        if n >= 5 and resilience_summary.provider_failure_rate > 0.50:
            status = HealthStatus.CRITICAL
            reasons.append(f"CRITICAL: High provider failure rate: {resilience_summary.provider_failure_rate * 100:.1f}%.")

        if n >= 5 and quality_summary.quality_pass_rate < 0.50:
            status = HealthStatus.CRITICAL
            reasons.append(f"CRITICAL: Quality pass rate below 50%: {quality_summary.quality_pass_rate * 100:.1f}%.")

        # DEGRADED conditions (if not already CRITICAL)
        if status != HealthStatus.CRITICAL:
            if latency_summary.total_latency.p95 > self.p95_latency_threshold:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: p95 latency ({latency_summary.total_latency.p95:.1f}ms) exceeds threshold ({self.p95_latency_threshold:.1f}ms).")

            if quality_summary.avg_quality_score < self.min_quality_score:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Average quality score ({quality_summary.avg_quality_score:.2f}) below threshold ({self.min_quality_score:.2f}).")

            if rag_count > 0 and rag_summary.citation_accuracy < self.min_citation_accuracy:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Citation accuracy ({rag_summary.citation_accuracy * 100:.1f}%) below threshold ({self.min_citation_accuracy * 100:.1f}%).")

            if rag_count > 0 and rag_summary.grounding_score < self.min_grounding_score:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Grounding score ({rag_summary.grounding_score * 100:.1f}%) below threshold ({self.min_grounding_score * 100:.1f}%).")

            if quality_summary.fallback_rate > self.max_fallback_rate:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Fallback rate ({quality_summary.fallback_rate * 100:.1f}%) exceeds threshold ({self.max_fallback_rate * 100:.1f}%).")

            if quality_summary.retry_rate > self.max_retry_rate:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Retry rate ({quality_summary.retry_rate * 100:.1f}%) exceeds threshold ({self.max_retry_rate * 100:.1f}%).")

            if resilience_summary.stream_interruption_rate > self.max_stream_interruption_rate:
                status = HealthStatus.DEGRADED
                reasons.append(f"DEGRADED: Stream interruption rate ({resilience_summary.stream_interruption_rate * 100:.1f}%) exceeds threshold ({self.max_stream_interruption_rate * 100:.1f}%).")

        if not reasons:
            reasons.append("All AI subsystem performance metrics and SLA thresholds are within nominal parameters.")

        return SystemHealthScorecard(
            status=status,
            time_window=time_window,
            sample_count=n,
            status_reasons=reasons,
            system=system_summary,
            latency=latency_summary,
            inference=inference_summary,
            rag=rag_summary,
            quality=quality_summary,
            resilience=resilience_summary,
            boundary=boundary_summary,
            observability_overhead_ms=avg_overhead,
        )
