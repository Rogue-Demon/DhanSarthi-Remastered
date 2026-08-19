"""
Lightweight, async-safe latency timing utility for DhanSarthi Phase L.7.1.

Uses Python monotonic perf_counter for sub-millisecond precision.
Supports nested timing, context managers, and zero-overhead disabled mode.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from app.ai.schemas.latency import LatencyBreakdown

logger = logging.getLogger(__name__)


class StepTimer:
    """Synchronous and asynchronous context manager for measuring step durations."""

    def __init__(self, tracker: LatencyTracker, step_name: str) -> None:
        self.tracker = tracker
        self.step_name = step_name
        self.start_time: float = 0.0

    def __enter__(self) -> StepTimer:
        if self.tracker.enabled:
            self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.tracker.enabled and self.start_time > 0.0:
            elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
            self.tracker.record(self.step_name, elapsed_ms)

    async def __aenter__(self) -> StepTimer:
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


class LatencyTracker:
    """
    Monotonic latency tracker instance attached per request lifecycle.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.breakdown = LatencyBreakdown()
        self._start_total: float = time.perf_counter() if enabled else 0.0

    def timer(self, step_name: str) -> StepTimer:
        """Return a context manager for timing a named execution step."""
        return StepTimer(self, step_name)

    def record(self, step_name: str, duration_ms: float) -> None:
        """Safely record a numeric millisecond timing field on LatencyBreakdown."""
        if not self.enabled:
            return
        try:
            val = max(0.0, float(duration_ms))
            if hasattr(self.breakdown, step_name):
                setattr(self.breakdown, step_name, val)
        except Exception as exc:
            logger.debug(f"Failed to record latency metric {step_name}: {exc}")

    def record_count(self, field_name: str, count: int) -> None:
        """Safely record an integer count field on LatencyBreakdown."""
        if not self.enabled:
            return
        try:
            if hasattr(self.breakdown, field_name):
                setattr(self.breakdown, field_name, int(count))
        except Exception as exc:
            logger.debug(f"Failed to record count metric {field_name}: {exc}")

    def record_flag(self, field_name: str, value: bool) -> None:
        """Safely record a boolean flag field on LatencyBreakdown."""
        if not self.enabled:
            return
        try:
            if hasattr(self.breakdown, field_name):
                setattr(self.breakdown, field_name, bool(value))
        except Exception as exc:
            logger.debug(f"Failed to record flag metric {field_name}: {exc}")

    def record_str(self, field_name: str, value: str) -> None:
        """Safely record a string metadata field on LatencyBreakdown (Phase L.7.3)."""
        if not self.enabled:
            return
        try:
            if hasattr(self.breakdown, field_name):
                setattr(self.breakdown, field_name, str(value))
        except Exception as exc:
            logger.debug(f"Failed to record string metric {field_name}: {exc}")

    def increment_count(self, field_name: str, delta: int = 1) -> None:
        """Atomically increment an integer count field on LatencyBreakdown (Phase L.7.3)."""
        if not self.enabled:
            return
        try:
            if hasattr(self.breakdown, field_name):
                current = getattr(self.breakdown, field_name, 0)
                setattr(self.breakdown, field_name, int(current) + delta)
        except Exception as exc:
            logger.debug(f"Failed to increment count metric {field_name}: {exc}")

    def finalize_total(self) -> float:
        """Compute and set total_ms for the complete lifecycle using perf_counter."""
        if not self.enabled or self._start_total <= 0.0:
            return 0.0
        try:
            total_ms = (time.perf_counter() - self._start_total) * 1000.0
            self.breakdown.total_ms = max(total_ms, 0.0)
            return self.breakdown.total_ms
        except Exception:
            return 0.0

    def finish(self) -> float:
        """Alias for finalize_total."""
        return self.finalize_total()

    @property
    def total_ms(self) -> float:
        """Return current total_ms."""
        self.finalize_total()
        return self.breakdown.total_ms

    def get_inference_tokens_per_second(self) -> float:
        """Calculate generated tokens per second based on recorded generation_ms."""
        gen_tokens = self.breakdown.generated_tokens or 0
        gen_ms = self.breakdown.generation_ms or 0.0
        if gen_ms > 0 and gen_tokens > 0:
            return round((gen_tokens / gen_ms) * 1000.0, 2)
        if self.breakdown.tokens_per_second is not None and self.breakdown.tokens_per_second > 0:
            return self.breakdown.tokens_per_second
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation of timings and metadata."""
        self.finalize_total()
        return self.breakdown.to_dict()
