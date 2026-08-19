"""
In-Memory Telemetry & Event Storage for DhanSarthi Phase L.10.

Thread-safe and async-safe local ring-buffer store with configurable max event capacity
and time-based retention pruning.
"""

from __future__ import annotations

import collections
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Deque, List, Optional

from app.ai.schemas.observability import AIRequestTelemetry, PipelineEvent, TimeWindow
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelemetryStore:
    """
    Thread-safe in-memory store for AI request telemetries and pipeline events.
    """

    def __init__(
        self,
        max_events: int = 10000,
        retention_hours: int = 24,
    ) -> None:
        self._max_events = max_events
        self._retention_hours = retention_hours
        self._lock = threading.Lock()
        self._telemetries: Deque[AIRequestTelemetry] = collections.deque(maxlen=max_events)
        self._events: Deque[PipelineEvent] = collections.deque(maxlen=max_events)

    def record_telemetry(self, telemetry: AIRequestTelemetry) -> None:
        """Store request telemetry thread-safely."""
        with self._lock:
            self._telemetries.append(telemetry)
            self._prune_expired()

    def record_event(self, event: PipelineEvent) -> None:
        """Store pipeline stage event thread-safely."""
        with self._lock:
            self._events.append(event)

    def record_events(self, events: List[PipelineEvent]) -> None:
        """Batch store pipeline stage events."""
        with self._lock:
            for ev in events:
                self._events.append(ev)

    def get_telemetries(
        self,
        window: Optional[TimeWindow] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[AIRequestTelemetry]:
        """
        Retrieve filtered telemetries based on time window or limit.
        """
        with self._lock:
            items = list(self._telemetries)

        now = datetime.now(timezone.utc)

        if since is not None:
            items = [t for t in items if t.timestamp >= since]
        elif window == TimeWindow.CURRENT:
            items = items[-1:] if items else []
        elif window == TimeWindow.RECENT:
            n = limit or 50
            items = items[-n:]
        elif window == TimeWindow.HOURLY:
            cutoff = now - timedelta(hours=1)
            items = [t for t in items if t.timestamp >= cutoff]
        elif window == TimeWindow.DAILY:
            cutoff = now - timedelta(days=1)
            items = [t for t in items if t.timestamp >= cutoff]

        if limit and limit > 0 and len(items) > limit:
            items = items[-limit:]

        return items

    def get_events_for_request(self, request_id: str) -> List[PipelineEvent]:
        """Retrieve all events matching a given request_id."""
        with self._lock:
            return [ev for ev in self._events if ev.request_id == request_id]

    def _prune_expired(self) -> None:
        """Internal prune for entries older than retention_hours (called under lock)."""
        if self._retention_hours <= 0 or not self._telemetries:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._retention_hours)
        while self._telemetries and self._telemetries[0].timestamp < cutoff:
            self._telemetries.popleft()

    def clear(self) -> None:
        """Clear all stored telemetries and events (useful in tests)."""
        with self._lock:
            self._telemetries.clear()
            self._events.clear()

    @property
    def total_records(self) -> int:
        with self._lock:
            return len(self._telemetries)


_GLOBAL_TELEMETRY_STORE: Optional[TelemetryStore] = None
_STORE_INIT_LOCK = threading.Lock()


def get_telemetry_store() -> TelemetryStore:
    """Return singleton instance of TelemetryStore."""
    global _GLOBAL_TELEMETRY_STORE
    if _GLOBAL_TELEMETRY_STORE is None:
        with _STORE_INIT_LOCK:
            if _GLOBAL_TELEMETRY_STORE is None:
                max_events = getattr(settings, "ai_observability_max_events", 10000)
                retention = getattr(settings, "ai_observability_retention_hours", 24)
                _GLOBAL_TELEMETRY_STORE = TelemetryStore(
                    max_events=max_events,
                    retention_hours=retention,
                )
    return _GLOBAL_TELEMETRY_STORE
