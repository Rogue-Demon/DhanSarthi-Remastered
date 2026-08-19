"""
Deterministic Retry Policy with Exponential Backoff and Jitter for Phase L.9.9.

Ensures that only transient upstream network/provider errors are retried,
while deterministic errors (400, 401, 403, safety rejections, client cancels)
fail fast without wasting resources.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from app.ai.schemas.resilience import ResilienceFailureType
from app.core.config import settings

logger = logging.getLogger(__name__)

# Failure types that are definitively retryable (transient)
_RETRYABLE_FAILURES: frozenset[ResilienceFailureType] = frozenset({
    ResilienceFailureType.RATE_LIMIT,
    ResilienceFailureType.PROVIDER_UNAVAILABLE,
    ResilienceFailureType.PROVIDER_TIMEOUT,
    ResilienceFailureType.NETWORK_TIMEOUT,
    ResilienceFailureType.GENERATION_TIMEOUT,
})

# Failure types that must NEVER be retried
_NON_RETRYABLE_FAILURES: frozenset[ResilienceFailureType] = frozenset({
    ResilienceFailureType.AUTHENTICATION,
    ResilienceFailureType.AUTHORIZATION,
    ResilienceFailureType.CLIENT_CANCELLED,
    ResilienceFailureType.MALFORMED_PROVIDER_RESPONSE,
    ResilienceFailureType.QUALITY_FAILURE,
    ResilienceFailureType.VALIDATION,
    ResilienceFailureType.UNKNOWN,
    ResilienceFailureType.NONE,
})


class RetryPolicy:
    """Deterministic retry evaluator for AI requests."""

    def __init__(
        self,
        max_retries: Optional[int] = None,
        base_backoff_seconds: Optional[float] = None,
        base_delay: Optional[float] = None,
        max_backoff_seconds: Optional[float] = None,
        max_delay: Optional[float] = None,
        jitter_seconds: Optional[float] = None,
        jitter_max: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.max_retries = max_retries if max_retries is not None else getattr(settings, "ai_max_retries", 2)
        
        base_d = base_backoff_seconds if base_backoff_seconds is not None else base_delay
        self.base_backoff_seconds = base_d if base_d is not None else 0.5

        max_d = max_backoff_seconds if max_backoff_seconds is not None else max_delay
        self.max_backoff_seconds = max_d if max_d is not None else getattr(settings, "ai_resilience_max_backoff_seconds", 4.0)

        jit_d = jitter_seconds if jitter_seconds is not None else jitter_max
        self.jitter_seconds = jit_d if jit_d is not None else getattr(settings, "ai_resilience_jitter_seconds", 0.25)

        self.enabled = enabled if enabled is not None else getattr(settings, "ai_resilience_enabled", True)

    def is_retryable(self, failure_type: ResilienceFailureType) -> bool:
        """Check if a classified failure type is eligible for retry."""
        if not self.enabled:
            return False
        return failure_type in _RETRYABLE_FAILURES

    def should_retry(self, failure_type: ResilienceFailureType, attempt_index: int) -> bool:
        """
        Evaluate whether another retry attempt is permitted.

        Args:
            failure_type: Standardized classification of the failure.
            attempt_index: 0-indexed count of retries already executed.

        Returns:
            True if retryable and attempts remaining; False otherwise.
        """
        if not self.is_retryable(failure_type):
            return False
        return attempt_index < self.max_retries

    def calculate_backoff(self, attempt_index: int) -> float:
        """
        Calculate backoff with exponential increase and random jitter.

        Formula:
          delay = min(max_backoff, base_backoff * (2 ** attempt_index)) + uniform(0, jitter)
        """
        exp_delay = self.base_backoff_seconds * (2 ** attempt_index)
        capped_delay = min(exp_delay, self.max_backoff_seconds)
        jitter = random.uniform(0.0, self.jitter_seconds) if self.jitter_seconds > 0 else 0.0
        return capped_delay + jitter
