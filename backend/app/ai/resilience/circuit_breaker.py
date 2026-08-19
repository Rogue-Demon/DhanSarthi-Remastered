"""
Thread-safe and Async-safe Circuit Breaker for Phase L.9.9 AI Resilience.

Guards external LLM provider calls against cascading failures.
Tracks consecutive failures, transitions to OPEN upon reaching threshold,
and tests recovery in HALF_OPEN state after cooldown period.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from app.ai.schemas.resilience import CircuitState, ResilienceFailureType
from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Thread-safe Circuit Breaker pattern implementation."""

    def __init__(
        self,
        name: str = "llm_provider",
        failure_threshold: Optional[int] = None,
        recovery_seconds: Optional[float] = None,
        recovery_timeout: Optional[float] = None,
        half_open_requests: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold or getattr(settings, "ai_circuit_failure_threshold", 5)
        
        rec_sec = recovery_seconds if recovery_seconds is not None else recovery_timeout
        self.recovery_seconds = rec_sec if rec_sec is not None else getattr(settings, "ai_circuit_recovery_seconds", 30.0)
        self.half_open_requests = half_open_requests or getattr(settings, "ai_circuit_half_open_requests", 1)
        self.enabled = enabled if enabled is not None else getattr(settings, "ai_circuit_breaker_enabled", True)

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._last_state_change = time.monotonic()
        self._half_open_probes_in_flight = 0
        self._last_failure_type = ResilienceFailureType.NONE

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state, automatically checking cooldown."""
        with self._lock:
            if not self.enabled:
                return CircuitState.CLOSED

            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._last_state_change
                if elapsed >= self.recovery_seconds:
                    logger.info(
                        f"CircuitBreaker[{self.name}] recovery timeout ({elapsed:.1f}s >= {self.recovery_seconds}s) "
                        "elapsed. Transitioning OPEN -> HALF_OPEN."
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._last_state_change = time.monotonic()
                    self._half_open_probes_in_flight = 0

            return self._state

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return self._consecutive_failures

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._consecutive_failures

    def can_execute(self) -> bool:
        """
        Check if execution is currently permitted.
        
        Returns:
            True if state is CLOSED or HALF_OPEN (with probe permit available).
            False if state is OPEN.
        """
        with self._lock:
            current_state = self.state

            if current_state == CircuitState.CLOSED:
                return True

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_probes_in_flight < self.half_open_requests:
                    self._half_open_probes_in_flight += 1
                    return True
                return False

            return False

    def record_success(self) -> None:
        """Record a successful provider request."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    f"CircuitBreaker[{self.name}] probe succeeded. Transitioning HALF_OPEN -> CLOSED."
                )
                self._state = CircuitState.CLOSED
                self._consecutive_failures = 0
                self._half_open_probes_in_flight = 0
                self._last_state_change = time.monotonic()
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    def record_failure(self, failure_type: ResilienceFailureType) -> None:
        """Record a failed provider request."""
        with self._lock:
            self._last_failure_type = failure_type

            # Only count external infrastructure/provider faults against breaker
            non_breaker_faults = {
                ResilienceFailureType.CLIENT_CANCELLED,
                ResilienceFailureType.VALIDATION,
                ResilienceFailureType.NONE,
            }
            if failure_type in non_breaker_faults:
                return

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"CircuitBreaker[{self.name}] probe failed with {failure_type.value}. Transitioning HALF_OPEN -> OPEN."
                )
                self._state = CircuitState.OPEN
                self._last_state_change = time.monotonic()
                self._half_open_probes_in_flight = 0
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.failure_threshold:
                    logger.warning(
                        f"CircuitBreaker[{self.name}] reached {self._consecutive_failures} failures "
                        f"(threshold={self.failure_threshold}). Transitioning CLOSED -> OPEN."
                    )
                    self._state = CircuitState.OPEN
                    self._last_state_change = time.monotonic()

    def reset(self) -> None:
        """Force reset the circuit breaker back to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._half_open_probes_in_flight = 0
            self._last_state_change = time.monotonic()
            self._last_failure_type = ResilienceFailureType.NONE


# Singleton instance for LLM provider
_global_circuit_breaker: Optional[CircuitBreaker] = None


def get_llm_circuit_breaker() -> CircuitBreaker:
    """Obtain or initialize the singleton LLM provider circuit breaker."""
    global _global_circuit_breaker
    if _global_circuit_breaker is None:
        _global_circuit_breaker = CircuitBreaker(name="llm_provider")
    return _global_circuit_breaker
