"""
Pydantic schemas and typed enums for Phase L.9.9 AI Production Resilience,
Failure Recovery & Graceful Degradation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ResilienceFailureType(str, Enum):
    """Categorized root failure classification for AI services."""
    NONE = "NONE"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
    MALFORMED_PROVIDER_RESPONSE = "MALFORMED_PROVIDER_RESPONSE"
    STREAM_INTERRUPTED = "STREAM_INTERRUPTED"
    CLIENT_CANCELLED = "CLIENT_CANCELLED"
    FAISS_FAILURE = "FAISS_FAILURE"
    PGVECTOR_FAILURE = "PGVECTOR_FAILURE"
    MINILM_FAILURE = "MINILM_FAILURE"
    RAG_FAILURE = "RAG_FAILURE"
    QUALITY_FAILURE = "QUALITY_FAILURE"
    VALIDATION = "VALIDATION"
    UNKNOWN = "UNKNOWN"


class CircuitState(str, Enum):
    """Circuit breaker operational state."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class FallbackType(str, Enum):
    """Type of graceful fallback employed."""
    NONE = "NONE"
    MODEL_FALLBACK = "MODEL_FALLBACK"
    PGVECTOR_FALLBACK = "PGVECTOR_FALLBACK"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"
    SAFE_FALLBACK = "SAFE_FALLBACK"


class ResilienceDecision(BaseModel):
    """Actionable decision returned by resilience policy after failure assessment."""
    should_retry: bool = Field(default=False, description="Whether transient error qualifies for safe retry")
    retry_count: int = Field(default=0, description="Current retry attempt index")
    failure_type: ResilienceFailureType = Field(default=ResilienceFailureType.NONE, description="Classified failure category")
    fallback_used: bool = Field(default=False, description="Whether fallback mechanism was triggered")
    fallback_type: FallbackType = Field(default=FallbackType.NONE, description="Classification of fallback employed")
    fallback_model: Optional[str] = Field(default=None, description="Alternative model candidate if model fallback")
    circuit_state: CircuitState = Field(default=CircuitState.CLOSED, description="Active state of the circuit breaker")
    reason: str = Field(default="", description="Sanitized rationale for resilience decision")


class ResilienceMetrics(BaseModel):
    """Runtime metrics and telemetry captured by the resilience subsystem."""
    retry_count: int = Field(default=0)
    fallback_used: bool = Field(default=False)
    fallback_type: FallbackType = Field(default=FallbackType.NONE)
    failure_type: ResilienceFailureType = Field(default=ResilienceFailureType.NONE)
    circuit_state: CircuitState = Field(default=CircuitState.CLOSED)
    provider_failure: bool = Field(default=False)
    rag_degraded: bool = Field(default=False)
    faiss_fallback: bool = Field(default=False)
    pgvector_fallback: bool = Field(default=False)
    minilm_fallback: bool = Field(default=False)
    stream_interrupted: bool = Field(default=False)
    client_cancelled: bool = Field(default=False)
    safe_fallback_used: bool = Field(default=False)
    recovery_time_ms: float = Field(default=0.0)

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Return sanitized dictionary suitable for message_metadata['resilience']."""
        return {
            "retry_count": self.retry_count,
            "fallback_used": self.fallback_used,
            "fallback_type": self.fallback_type.value if isinstance(self.fallback_type, FallbackType) else str(self.fallback_type),
            "failure_type": self.failure_type.value if isinstance(self.failure_type, ResilienceFailureType) else str(self.failure_type),
            "circuit_state": self.circuit_state.value if isinstance(self.circuit_state, CircuitState) else str(self.circuit_state),
            "provider_failure": self.provider_failure,
            "rag_degraded": self.rag_degraded,
            "stream_interrupted": self.stream_interrupted,
            "client_cancelled": self.client_cancelled,
            "safe_fallback_used": self.safe_fallback_used,
            "recovery_time_ms": round(self.recovery_time_ms, 2),
        }
