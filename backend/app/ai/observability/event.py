"""
Pipeline Stage Event Tracking for DhanSarthi Phase L.10.

Captures timestamped, privacy-safe lifecycle transitions for individual AI requests.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.ai.observability.privacy import sanitize_metadata_dict
from app.ai.schemas.observability import PipelineEvent, PipelineEventType

logger = logging.getLogger(__name__)


class PipelineEventTracker:
    """
    Per-request lifecycle event recorder.
    Maintains a chronological log of stage transitions with monotonic elapsed timings.
    """

    def __init__(self, request_id: str, enabled: bool = True) -> None:
        self.request_id = request_id
        self.enabled = enabled
        self._start_perf: float = time.perf_counter()
        self._events: List[PipelineEvent] = []

    def record_event(
        self,
        event_type: PipelineEventType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[PipelineEvent]:
        """
        Record a lifecycle transition event with elapsed milliseconds.
        """
        if not self.enabled:
            return None

        try:
            elapsed_ms = (time.perf_counter() - self._start_perf) * 1000.0
            safe_meta = sanitize_metadata_dict(metadata)
            event = PipelineEvent(
                request_id=self.request_id,
                event_type=event_type,
                elapsed_ms=round(elapsed_ms, 2),
                metadata=safe_meta,
            )
            self._events.append(event)
            return event
        except Exception as exc:
            logger.debug(f"Failed to record pipeline event {event_type}: {exc}")
            return None

    def get_events(self) -> List[PipelineEvent]:
        """Return all recorded events for this request."""
        return list(self._events)
