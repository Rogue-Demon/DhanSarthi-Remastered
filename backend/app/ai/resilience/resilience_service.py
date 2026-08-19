"""
Resilience Service for Phase L.9.9.

Centralized coordinator for failure classification, circuit breaking, deterministic
retries, model fallbacks, safe error formatting, and deterministic fallback responses.
Contains no business logic; acts strictly as an operational reliability shell.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set

from app.ai.resilience.circuit_breaker import CircuitBreaker, get_llm_circuit_breaker
from app.ai.resilience.provider_fallback import (
    ModelFallbackCoordinator,
    classify_provider_failure,
    sanitize_error_message,
)
from app.ai.resilience.rag_fallback import RAGDegradationCoordinator
from app.ai.resilience.retry_policy import RetryPolicy
from app.ai.resilience.streaming_recovery import StreamingRecoveryManager
from app.ai.schemas.resilience import (
    CircuitState,
    FallbackType,
    ResilienceDecision,
    ResilienceFailureType,
    ResilienceMetrics,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standardized deterministic fallback messages (no LLM generation)
_FALLBACK_MESSAGES = {
    ResilienceFailureType.PROVIDER_UNAVAILABLE: (
        "I'm temporarily unable to generate an AI response. Please try again in a moment."
    ),
    ResilienceFailureType.RATE_LIMIT: (
        "The AI advisor is experiencing high demand right now. Please wait a few seconds and try again."
    ),
    ResilienceFailureType.PROVIDER_TIMEOUT: (
        "The response took longer than expected to generate. Please try asking again in a moment."
    ),
    ResilienceFailureType.GENERATION_TIMEOUT: (
        "The response generation timed out. Please try again with a shorter or more specific question."
    ),
    ResilienceFailureType.NETWORK_TIMEOUT: (
        "A network timeout occurred while connecting to the AI provider. Please check your connection and retry."
    ),
    ResilienceFailureType.AUTHENTICATION: (
        "The AI service is currently undergoing maintenance. Please try again later."
    ),
    ResilienceFailureType.AUTHORIZATION: (
        "Access to this AI model resource is currently restricted. Please try again later."
    ),
    "PERSONAL_FINANCE_UNAVAILABLE": (
        "I couldn't retrieve your financial data right now. I don't want to guess at your numbers. Please try again shortly."
    ),
    "RAG_GROUNDING_UNAVAILABLE": (
        "I couldn't retrieve the authoritative information needed to answer this reliably right now."
    ),
    "GENERAL_SAFE_FALLBACK": (
        "I encountered a temporary issue generating your response. Please try again in a moment."
    ),
}


class ResilienceService:
    """
    Core resilience coordinator for DhanSarthi AI Advisor.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        model_fallback: Optional[ModelFallbackCoordinator] = None,
        rag_fallback: Optional[RAGDegradationCoordinator] = None,
        streaming_recovery: Optional[StreamingRecoveryManager] = None,
    ) -> None:
        self.enabled = getattr(settings, "ai_resilience_enabled", True)
        self.circuit_breaker = circuit_breaker or get_llm_circuit_breaker()
        self.retry_policy = retry_policy or RetryPolicy()
        self.model_fallback = model_fallback or ModelFallbackCoordinator()
        self.rag_fallback = rag_fallback or RAGDegradationCoordinator()
        self.streaming_recovery = streaming_recovery or StreamingRecoveryManager()
        self.max_total_attempts = getattr(settings, "ai_max_total_attempts", 3)

    def classify_failure(self, exc: Exception) -> ResilienceFailureType:
        """Classify any exception into a standardized ResilienceFailureType."""
        return classify_provider_failure(exc)

    def can_execute_llm(self) -> bool:
        """Check whether the circuit breaker permits LLM execution."""
        if not self.enabled:
            return True
        return self.circuit_breaker.can_execute()

    def get_circuit_state(self) -> CircuitState:
        """Get active circuit state."""
        return self.circuit_breaker.state

    def record_llm_success(self) -> None:
        """Record successful LLM invocation in circuit breaker."""
        if self.enabled:
            self.circuit_breaker.record_success()

    def record_llm_failure(self, failure_type: ResilienceFailureType) -> None:
        """Record failure in circuit breaker."""
        if self.enabled:
            self.circuit_breaker.record_failure(failure_type)

    def should_retry(self, failure_type: ResilienceFailureType, attempt_index: int) -> bool:
        """Assess whether a transient failure should be retried."""
        if not self.enabled:
            return False
        return self.retry_policy.should_retry(failure_type, attempt_index)

    def get_retry_backoff(self, attempt_index: int) -> float:
        """Get exponential backoff delay with jitter."""
        return self.retry_policy.calculate_backoff(attempt_index)

    def get_fallback_model(self, current_model: str, attempted_models: Optional[Set[str]] = None) -> Optional[str]:
        """Obtain the next allowed model candidate on transient provider failure."""
        if not self.enabled:
            return None
        return self.model_fallback.get_fallback_model(current_model, attempted_models)

    def get_safe_fallback_message(
        self,
        failure_type: Optional[ResilienceFailureType] = None,
        context_type: str = "general",
    ) -> str:
        """
        Produce a deterministic fallback response without invoking the LLM.
        """
        if context_type == "personal_finance":
            return _FALLBACK_MESSAGES["PERSONAL_FINANCE_UNAVAILABLE"]

        if context_type == "rag_grounding":
            return _FALLBACK_MESSAGES["RAG_GROUNDING_UNAVAILABLE"]

        if failure_type and failure_type in _FALLBACK_MESSAGES:
            return _FALLBACK_MESSAGES[failure_type]

        return _FALLBACK_MESSAGES["GENERAL_SAFE_FALLBACK"]

    def sanitize_error(self, exc: Exception) -> str:
        """Remove secrets/tokens from exception messages."""
        return sanitize_error_message(exc)


# Singleton factory for ResilienceService
_global_resilience_service: Optional[ResilienceService] = None


def get_resilience_service() -> ResilienceService:
    """Get or create singleton instance of ResilienceService."""
    global _global_resilience_service
    if _global_resilience_service is None:
        _global_resilience_service = ResilienceService()
    return _global_resilience_service
