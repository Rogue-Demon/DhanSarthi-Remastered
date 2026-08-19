"""
Phase L.9.9 AI Production Resilience, Failure Recovery & Graceful Degradation.
"""

from app.ai.resilience.circuit_breaker import CircuitBreaker, get_llm_circuit_breaker
from app.ai.resilience.provider_fallback import (
    ModelFallbackCoordinator,
    classify_provider_failure,
    sanitize_error_message,
)
from app.ai.resilience.rag_fallback import RAGDegradationCoordinator
from app.ai.resilience.resilience_service import (
    ResilienceService,
    get_resilience_service,
)
from app.ai.resilience.retry_policy import RetryPolicy
from app.ai.resilience.streaming_recovery import (
    StreamingRecoveryManager,
    format_sse_error_event,
)
from app.ai.schemas.resilience import (
    CircuitState,
    FallbackType,
    ResilienceDecision,
    ResilienceFailureType,
    ResilienceMetrics,
)

__all__ = [
    "CircuitBreaker",
    "get_llm_circuit_breaker",
    "CircuitState",
    "FallbackType",
    "ResilienceDecision",
    "ResilienceFailureType",
    "ResilienceMetrics",
    "RetryPolicy",
    "ModelFallbackCoordinator",
    "classify_provider_failure",
    "sanitize_error_message",
    "RAGDegradationCoordinator",
    "StreamingRecoveryManager",
    "format_sse_error_event",
    "ResilienceService",
    "get_resilience_service",
]
