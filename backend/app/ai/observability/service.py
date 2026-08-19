"""
Production AI Observability Service for DhanSarthi Phase L.10.

Main orchestrator for request correlation, privacy-safe telemetry recording,
lifecycle event tracking, and SLA health scorecard generation.
Failure-safe by design: All observability calls are isolated and will never raise
exceptions to the user or impact normal request handling.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.ai.observability.aggregator import MetricsAggregator
from app.ai.observability.event import PipelineEventTracker
from app.ai.observability.metrics import TelemetryBuilder
from app.ai.observability.privacy import hash_identifier, sanitize_metadata_dict
from app.ai.observability.store import TelemetryStore, get_telemetry_store
from app.ai.schemas.latency import LatencyBreakdown
from app.ai.schemas.observability import (
    AIRequestTelemetry,
    PipelineEvent,
    PipelineEventType,
    SystemHealthScorecard,
    TimeWindow,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ObservabilityService:
    """
    Production-grade AI Observability Service providing non-blocking metric recording
    and SLA health evaluation.
    """

    def __init__(
        self,
        store: Optional[TelemetryStore] = None,
        aggregator: Optional[MetricsAggregator] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.store = store or get_telemetry_store()
        self.aggregator = aggregator or MetricsAggregator()
        self.enabled = enabled if enabled is not None else getattr(settings, "ai_observability_enabled", True)

    def create_request_tracker(self, request_id: Optional[str] = None) -> Tuple[str, PipelineEventTracker]:
        """
        Generate or validate a unique request correlation ID and return an attached event tracker.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        tracker = PipelineEventTracker(request_id=req_id, enabled=self.enabled)
        tracker.record_event(PipelineEventType.REQUEST_STARTED)
        return req_id, tracker

    def record_request_telemetry(
        self,
        request_id: str,
        conversation_id: Optional[Any] = None,
        latency_breakdown: Optional[LatencyBreakdown] = None,
        understanding: Optional[Any] = None,
        quality_metadata: Optional[Dict[str, Any]] = None,
        resilience_metadata: Optional[Dict[str, Any]] = None,
        routing_decision: Optional[Any] = None,
        streaming_enabled: bool = False,
        personal_boundary_checked: bool = False,
        personal_boundary_passed: bool = True,
        pipeline_events: Optional[List[PipelineEvent]] = None,
    ) -> Optional[AIRequestTelemetry]:
        """
        Build, sanitize, and persist request telemetry record.
        Wrapped in comprehensive try/except for absolute failure isolation.
        """
        if not self.enabled:
            return None

        t0 = time.perf_counter()
        try:
            telemetry = TelemetryBuilder.build(
                request_id=request_id,
                conversation_id=conversation_id,
                latency_breakdown=latency_breakdown,
                understanding=understanding,
                quality_metadata=quality_metadata,
                resilience_metadata=resilience_metadata,
                routing_decision=routing_decision,
                streaming_enabled=streaming_enabled,
                personal_boundary_checked=personal_boundary_checked,
                personal_boundary_passed=personal_boundary_passed,
                overhead_ms=(time.perf_counter() - t0) * 1000.0,
            )

            self.store.record_telemetry(telemetry)

            if pipeline_events:
                self.store.record_events(pipeline_events)

            return telemetry
        except Exception as exc:
            logger.warning(f"Failed to record AI telemetry for request {request_id}: {exc}", exc_info=False)
            return None

    def get_health_scorecard(
        self,
        time_window: TimeWindow = TimeWindow.RECENT,
        limit: Optional[int] = None,
    ) -> SystemHealthScorecard:
        """
        Generate aggregated SystemHealthScorecard over selected time window.
        """
        try:
            telemetries = self.store.get_telemetries(window=time_window, limit=limit)
            return self.aggregator.aggregate(telemetries, time_window=time_window)
        except Exception as exc:
            logger.error(f"Failed to generate health scorecard: {exc}", exc_info=True)
            return SystemHealthScorecard(
                time_window=time_window,
                status_reasons=[f"Scorecard generation failed: {exc}"],
            )

    def get_recent_summary(self, limit: int = 50) -> Dict[str, Any]:
        """Return dict representation of recent health scorecard."""
        card = self.get_health_scorecard(time_window=TimeWindow.RECENT, limit=limit)
        return card.model_dump()

    def get_hourly_summary(self) -> Dict[str, Any]:
        """Return dict representation of last 1 hour health scorecard."""
        card = self.get_health_scorecard(time_window=TimeWindow.HOURLY)
        return card.model_dump()

    def get_daily_summary(self) -> Dict[str, Any]:
        """Return dict representation of last 24 hours health scorecard."""
        card = self.get_health_scorecard(time_window=TimeWindow.DAILY)
        return card.model_dump()

    def clear_store(self) -> None:
        """Clear all stored telemetries (useful for test resets)."""
        self.store.clear()


_GLOBAL_OBSERVABILITY_SERVICE: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """Return singleton instance of ObservabilityService."""
    global _GLOBAL_OBSERVABILITY_SERVICE
    if _GLOBAL_OBSERVABILITY_SERVICE is None:
        _GLOBAL_OBSERVABILITY_SERVICE = ObservabilityService()
    return _GLOBAL_OBSERVABILITY_SERVICE
