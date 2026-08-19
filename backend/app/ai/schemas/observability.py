"""
Production AI Observability Schemas for DhanSarthi Phase L.10.

Defines privacy-safe, strongly typed data models for telemetry events, request telemetry,
and production AI health scorecards.

Privacy Guarantee:
No prompts, user queries, financial figures, credentials, or raw responses are stored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.schemas.evaluation_metrics import PercentileDistribution, RAGEvaluationSummary


class HealthStatus(str, Enum):
    """Overall status of the AI subsystem."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class TimeWindow(str, Enum):
    """Aggregation time windows."""

    CURRENT = "CURRENT"
    RECENT = "RECENT"
    HOURLY = "HOURLY"
    DAILY = "DAILY"


class PipelineEventType(str, Enum):
    """Major internal pipeline stage transition events."""

    REQUEST_STARTED = "REQUEST_STARTED"
    QUERY_UNDERSTANDING_COMPLETED = "QUERY_UNDERSTANDING_COMPLETED"
    RETRIEVAL_COMPLETED = "RETRIEVAL_COMPLETED"
    RERANKING_COMPLETED = "RERANKING_COMPLETED"
    CONTEXT_BUILT = "CONTEXT_BUILT"
    PROMPT_COMPRESSED = "PROMPT_COMPRESSED"
    MODEL_SELECTED = "MODEL_SELECTED"
    LLM_STARTED = "LLM_STARTED"
    FIRST_TOKEN_RECEIVED = "FIRST_TOKEN_RECEIVED"
    LLM_COMPLETED = "LLM_COMPLETED"
    SAFETY_COMPLETED = "SAFETY_COMPLETED"
    QUALITY_COMPLETED = "QUALITY_COMPLETED"
    RETRY_STARTED = "RETRY_STARTED"
    FALLBACK_USED = "FALLBACK_USED"
    STREAM_INTERRUPTED = "STREAM_INTERRUPTED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    REQUEST_FAILED = "REQUEST_FAILED"


class PipelineEvent(BaseModel):
    """Single stage-transition event in the AI execution lifecycle."""

    request_id: str = Field(description="Unique correlation ID for the request")
    event_type: PipelineEventType = Field(description="Stage event type")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    elapsed_ms: float = Field(default=0.0, description="Elapsed time since request start in ms")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Safe structured metadata (no secrets/PII)")


class AIRequestTelemetry(BaseModel):
    """
    Privacy-safe, comprehensive request telemetry record.
    Captures performance, routing, retrieval, quality, and resilience metrics.
    """

    request_id: str = Field(description="Unique request correlation ID")
    conversation_id_hash: Optional[str] = Field(default=None, description="One-way salted hash of conversation ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query_category: Optional[str] = Field(default=None)
    intent: Optional[str] = Field(default=None)
    scope: Optional[str] = Field(default=None)
    operation_type: Optional[str] = Field(default=None)

    # Retrieval & Semantic Intelligence
    retrieval_strategy: Optional[str] = Field(default=None)
    semantic_strategy: Optional[str] = Field(default=None)
    pgvector_used: bool = Field(default=False)
    faiss_used: bool = Field(default=False)
    minilm_used: bool = Field(default=False)
    rag_candidate_count: int = Field(default=0)
    rag_selected_count: int = Field(default=0)

    # Inference & Model Selection
    selected_model: Optional[str] = Field(default=None)
    model_routing_reason: Optional[str] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    generated_tokens: Optional[int] = Field(default=None)
    tokens_per_second: Optional[float] = Field(default=None)

    # Latency Breakdown
    ttft_ms: Optional[float] = Field(default=None)
    provider_network_ms: Optional[float] = Field(default=None)
    generation_ms: Optional[float] = Field(default=None)
    total_ms: float = Field(default=0.0)

    # Quality & Grounding
    quality_overall_score: Optional[float] = Field(default=None)
    quality_passed: Optional[bool] = Field(default=None)
    quality_retry_used: bool = Field(default=False)
    citation_accuracy: Optional[float] = Field(default=None)
    authority_accuracy: Optional[float] = Field(default=None)
    grounding_score: Optional[float] = Field(default=None)

    # Retrieval Evaluation (Hit@K & MRR)
    rag_hit_at_1: Optional[bool] = Field(default=None)
    rag_hit_at_3: Optional[bool] = Field(default=None)
    rag_hit_at_5: Optional[bool] = Field(default=None)
    rag_mrr: Optional[float] = Field(default=None)

    # Resilience & Fault Tolerance
    resilience_failure_type: Optional[str] = Field(default="NONE")
    circuit_state: str = Field(default="CLOSED")
    fallback_used: bool = Field(default=False)
    fallback_type: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)

    # Streaming UX
    streaming_enabled: bool = Field(default=False)
    stream_interrupted: bool = Field(default=False)
    client_cancelled: bool = Field(default=False)

    # Personal Finance Boundary Compliance
    personal_boundary_checked: bool = Field(default=False)
    personal_boundary_passed: bool = Field(default=True)

    # Observability Overhead
    observability_overhead_ms: float = Field(default=0.0)


# ------------------------------------------------------------------------------
# Health Scorecard Models
# ------------------------------------------------------------------------------

class SystemHealthSummary(BaseModel):
    total_requests: int = Field(default=0)
    successful_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)
    success_rate: float = Field(default=1.0)


class LatencyHealthSummary(BaseModel):
    total_latency: PercentileDistribution = Field(default_factory=PercentileDistribution)
    ttft_latency: PercentileDistribution = Field(default_factory=PercentileDistribution)
    generation_latency: PercentileDistribution = Field(default_factory=PercentileDistribution)
    provider_network_latency: PercentileDistribution = Field(default_factory=PercentileDistribution)


class InferenceHealthSummary(BaseModel):
    avg_tokens_per_second: float = Field(default=0.0)
    avg_prompt_tokens: float = Field(default=0.0)
    avg_generated_tokens: float = Field(default=0.0)
    model_distribution: Dict[str, int] = Field(default_factory=dict)
    routing_reason_distribution: Dict[str, int] = Field(default_factory=dict)


class QualityHealthSummary(BaseModel):
    quality_pass_rate: float = Field(default=1.0)
    avg_quality_score: float = Field(default=1.0)
    retry_rate: float = Field(default=0.0)
    fallback_rate: float = Field(default=0.0)


class ResilienceHealthSummary(BaseModel):
    circuit_breaker_state: str = Field(default="CLOSED")
    circuit_breaker_trips: int = Field(default=0)
    provider_failure_count: int = Field(default=0)
    provider_failure_rate: float = Field(default=0.0)
    model_fallback_count: int = Field(default=0)
    model_fallback_rate: float = Field(default=0.0)
    safe_fallback_count: int = Field(default=0)
    safe_fallback_rate: float = Field(default=0.0)
    stream_interruption_count: int = Field(default=0)
    stream_interruption_rate: float = Field(default=0.0)
    client_cancellation_count: int = Field(default=0)


class BoundaryHealthSummary(BaseModel):
    personal_boundary_checks: int = Field(default=0)
    personal_boundary_passes: int = Field(default=0)
    personal_boundary_failures: int = Field(default=0)
    boundary_compliance_rate: float = Field(default=1.0)
    safety_validation_pass_rate: float = Field(default=1.0)


class SystemHealthScorecard(BaseModel):
    """Production AI Health Scorecard containing holistic telemetry and SLA evaluation."""

    status: HealthStatus = Field(default=HealthStatus.HEALTHY)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_window: TimeWindow = Field(default=TimeWindow.RECENT)
    sample_count: int = Field(default=0)
    status_reasons: List[str] = Field(default_factory=list)

    system: SystemHealthSummary = Field(default_factory=SystemHealthSummary)
    latency: LatencyHealthSummary = Field(default_factory=LatencyHealthSummary)
    inference: InferenceHealthSummary = Field(default_factory=InferenceHealthSummary)
    rag: RAGEvaluationSummary = Field(default_factory=RAGEvaluationSummary)
    quality: QualityHealthSummary = Field(default_factory=QualityHealthSummary)
    resilience: ResilienceHealthSummary = Field(default_factory=ResilienceHealthSummary)
    boundary: BoundaryHealthSummary = Field(default_factory=BoundaryHealthSummary)
    observability_overhead_ms: float = Field(default=0.0)
