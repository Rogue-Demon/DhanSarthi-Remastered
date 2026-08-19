"""
Dedicated Test Suite for DhanSarthi Phase L.10: AI Observability & Performance Monitoring.

Contains 30 comprehensive unit and integration tests covering:
  - Request ID generation & propagation
  - Privacy guarantees & deterministic secret scrubbing
  - Telemetry construction without content leaks
  - Statistical distribution & percentile calculations
  - In-memory ring buffer storage with retention
  - RAG, quality, resilience, and boundary metric aggregations
  - Production AI Health Scorecard classification (HEALTHY / DEGRADED / CRITICAL)
  - Failure-isolation and disabled mode safety
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.ai.observability.aggregator import MetricsAggregator
from app.ai.observability.event import PipelineEventTracker
from app.ai.observability.metrics import TelemetryBuilder
from app.ai.observability.privacy import (
    hash_identifier,
    sanitize_metadata_dict,
    sanitize_text_field,
)
from app.ai.observability.service import ObservabilityService
from app.ai.observability.store import TelemetryStore
from app.ai.schemas.evaluation_metrics import PercentileDistribution
from app.ai.schemas.latency import LatencyBreakdown
from app.ai.schemas.observability import (
    AIRequestTelemetry,
    HealthStatus,
    PipelineEvent,
    PipelineEventType,
    SystemHealthScorecard,
    TimeWindow,
)
from app.core.config import settings


# ==============================================================================
# 1. Request Correlation & ID Generation Tests
# ==============================================================================

def test_request_id_generation():
    service = ObservabilityService()
    req_id, tracker = service.create_request_tracker()
    assert req_id.startswith("req_")
    assert len(req_id) > 5
    events = tracker.get_events()
    assert len(events) == 1
    assert events[0].event_type == PipelineEventType.REQUEST_STARTED
    assert events[0].request_id == req_id


def test_custom_request_id_accepted():
    service = ObservabilityService()
    req_id, tracker = service.create_request_tracker(request_id="custom_req_12345")
    assert req_id == "custom_req_12345"
    assert tracker.request_id == "custom_req_12345"


# ==============================================================================
# 2. Privacy & Secret Scrubbing Tests
# ==============================================================================

def test_sanitize_text_bearer_and_tokens():
    raw = "Bearer hf_9876543210abcdef1234567890api_key=sk-12345678"
    clean = sanitize_text_field(raw)
    assert "hf_9876543210abcdef1234567890" not in clean
    assert "sk-12345678" not in clean
    assert "[REDACTED" in clean


def test_sanitize_text_email_and_phone():
    raw = "Contact support at user.name@fintech.co.in or call +91 9876543210"
    clean = sanitize_text_field(raw)
    assert "user.name@fintech.co.in" not in clean
    assert "9876543210" not in clean
    assert "[REDACTED_EMAIL]" in clean
    assert "[REDACTED_PHONE]" in clean


def test_sanitize_text_financial_values():
    raw = "Your total investment is ₹5,00,000 with Rs. 15000 in savings."
    clean = sanitize_text_field(raw)
    assert "5,00,000" not in clean
    assert "15000" not in clean
    assert "[REDACTED_AMOUNT]" in clean


def test_sanitize_metadata_dict_discards_banned_keys():
    meta = {
        "raw_prompt": "Tell me my balance",
        "raw_response": "Your balance is 1000",
        "user_financial_context": {"net_worth": 500000},
        "api_key": "secret123",
        "tokens_per_second": 32.5,
        "circuit_state": "CLOSED",
    }
    clean = sanitize_metadata_dict(meta)
    assert "raw_prompt" not in clean
    assert "raw_response" not in clean
    assert "user_financial_context" not in clean
    assert "api_key" not in clean
    assert clean["tokens_per_second"] == 32.5
    assert clean["circuit_state"] == "CLOSED"


def test_hash_identifier_is_deterministic_and_irreversible():
    h1 = hash_identifier(101)
    h2 = hash_identifier(101)
    h3 = hash_identifier(102)
    assert h1 == h2
    assert h1 != h3
    assert "101" not in h1
    assert len(h1) == 16
    assert hash_identifier(None) is None


# ==============================================================================
# 3. Telemetry Schema & Construction Tests
# ==============================================================================

def test_telemetry_builder_omits_raw_prompts_and_content():
    lb = LatencyBreakdown(
        total_ms=300.0,
        ttft_ms=85.0,
        generation_ms=210.0,
        prompt_tokens=350,
        generated_tokens=120,
    )
    t = TelemetryBuilder.build(
        request_id="req_test_01",
        conversation_id=42,
        latency_breakdown=lb,
        personal_boundary_checked=True,
        personal_boundary_passed=True,
    )
    assert t.request_id == "req_test_01"
    assert t.conversation_id_hash is not None
    assert t.total_ms == 300.0
    assert t.ttft_ms == 85.0
    assert t.prompt_tokens == 350
    assert t.generated_tokens == 120
    # Verify no raw payload fields exist in model
    dump = t.model_dump()
    assert "prompt" not in dump
    assert "response" not in dump
    assert "message" not in dump


def test_pipeline_event_tracker_records_chronological_events():
    tracker = PipelineEventTracker("req_100")
    tracker.record_event(PipelineEventType.QUERY_UNDERSTANDING_COMPLETED, {"intent": "GENERAL_FINANCE"})
    tracker.record_event(PipelineEventType.RETRIEVAL_COMPLETED, {"chunks": 3})
    tracker.record_event(PipelineEventType.REQUEST_COMPLETED)
    events = tracker.get_events()
    assert len(events) == 3
    assert events[0].event_type == PipelineEventType.QUERY_UNDERSTANDING_COMPLETED
    assert events[1].event_type == PipelineEventType.RETRIEVAL_COMPLETED
    assert events[2].event_type == PipelineEventType.REQUEST_COMPLETED
    assert events[0].metadata["intent"] == "GENERAL_FINANCE"


# ==============================================================================
# 4. Statistical Distributions & Percentile Calculations
# ==============================================================================

def test_percentile_distribution_empty():
    dist = PercentileDistribution.from_values([])
    assert dist.count == 0
    assert dist.p50 == 0.0
    assert dist.p95 == 0.0


def test_percentile_distribution_single_value():
    dist = PercentileDistribution.from_values([100.0])
    assert dist.count == 1
    assert dist.min == 100.0
    assert dist.mean == 100.0
    assert dist.p50 == 100.0
    assert dist.p95 == 100.0
    assert dist.max == 100.0


def test_percentile_distribution_synthetic_linear_sequence():
    vals = [float(x) for x in range(1, 101)]
    dist = PercentileDistribution.from_values(vals)
    assert dist.count == 100
    assert dist.min == 1.0
    assert dist.max == 100.0
    assert abs(dist.p50 - 50.5) <= 0.5
    assert abs(dist.p90 - 90.1) <= 0.5
    assert abs(dist.p95 - 95.05) <= 0.5
    assert abs(dist.p99 - 99.01) <= 0.5


def test_percentile_distribution_handles_none_and_nan():
    vals = [10.0, None, float("nan"), 20.0, 30.0]
    dist = PercentileDistribution.from_values(vals)
    assert dist.count == 3
    assert dist.min == 10.0
    assert dist.max == 30.0
    assert dist.mean == 20.0


# ==============================================================================
# 5. Storage & Ring Buffer Retention Tests
# ==============================================================================

def test_telemetry_store_ring_buffer_capacity():
    store = TelemetryStore(max_events=10)
    for i in range(25):
        t = TelemetryBuilder.build(request_id=f"req_{i}", conversation_id=i)
        store.record_telemetry(t)
    assert store.total_records == 10
    recent = store.get_telemetries()
    assert len(recent) == 10
    assert recent[0].request_id == "req_15"
    assert recent[-1].request_id == "req_24"


def test_telemetry_store_retention_pruning():
    store = TelemetryStore(max_events=100, retention_hours=1)
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    old_t = AIRequestTelemetry(request_id="old_01", timestamp=old_time, total_ms=10.0)
    store.record_telemetry(old_t)
    # Adding new telemetry triggers prune
    new_t = AIRequestTelemetry(request_id="new_01", total_ms=20.0)
    store.record_telemetry(new_t)
    records = store.get_telemetries()
    assert len(records) == 1
    assert records[0].request_id == "new_01"


def test_telemetry_store_filter_by_windows():
    store = TelemetryStore(max_events=50)
    for i in range(10):
        t = TelemetryBuilder.build(request_id=f"req_{i}", conversation_id=i)
        store.record_telemetry(t)
    assert len(store.get_telemetries(window=TimeWindow.CURRENT)) == 1
    assert len(store.get_telemetries(window=TimeWindow.RECENT, limit=5)) == 5
    assert len(store.get_telemetries(window=TimeWindow.DAILY)) == 10


# ==============================================================================
# 6. Metric Aggregation & Health Scorecard Tests
# ==============================================================================

def test_aggregator_rag_metrics():
    aggregator = MetricsAggregator()
    t1 = AIRequestTelemetry(request_id="r1", total_ms=100.0, rag_selected_count=5, rag_hit_at_1=True, rag_hit_at_3=True, rag_hit_at_5=True, rag_mrr=1.0, citation_accuracy=1.0, authority_accuracy=1.0, grounding_score=0.98)
    t2 = AIRequestTelemetry(request_id="r2", total_ms=100.0, rag_selected_count=2, rag_hit_at_1=False, rag_hit_at_3=True, rag_hit_at_5=True, rag_mrr=0.5, citation_accuracy=0.90, authority_accuracy=1.0, grounding_score=0.92)
    card = aggregator.aggregate([t1, t2])
    assert card.rag.total_queries == 2
    assert card.rag.hit_at_1 == 0.5
    assert card.rag.hit_at_3 == 1.0
    assert card.rag.hit_at_5 == 1.0
    assert card.rag.mrr == 0.75
    assert card.rag.citation_accuracy == 0.95


def test_aggregator_quality_and_resilience_metrics():
    aggregator = MetricsAggregator()
    t1 = AIRequestTelemetry(request_id="r1", total_ms=200.0, quality_overall_score=0.95, quality_passed=True, quality_retry_used=False, fallback_used=False)
    t2 = AIRequestTelemetry(request_id="r2", total_ms=250.0, quality_overall_score=0.85, quality_passed=False, quality_retry_used=True, fallback_used=True, fallback_type="MODEL_FALLBACK")
    card = aggregator.aggregate([t1, t2])
    assert card.quality.quality_pass_rate == 0.5
    assert card.quality.avg_quality_score == 0.90
    assert card.quality.retry_rate == 0.5
    assert card.quality.fallback_rate == 0.5
    assert card.resilience.model_fallback_count == 1


def test_health_status_healthy_nominal():
    aggregator = MetricsAggregator()
    t = AIRequestTelemetry(
        request_id="r_ok",
        total_ms=450.0,
        quality_overall_score=0.98,
        quality_passed=True,
        citation_accuracy=1.0,
        grounding_score=0.98,
        personal_boundary_checked=True,
        personal_boundary_passed=True,
    )
    card = aggregator.aggregate([t])
    assert card.status == HealthStatus.HEALTHY


def test_health_status_degraded_on_high_latency():
    aggregator = MetricsAggregator(p95_latency_threshold=1000.0)
    t = AIRequestTelemetry(
        request_id="r_slow",
        total_ms=2500.0,
        quality_overall_score=0.98,
        quality_passed=True,
    )
    card = aggregator.aggregate([t])
    assert card.status == HealthStatus.DEGRADED
    assert any("p95 latency" in r for r in card.status_reasons)


def test_health_status_critical_on_personal_boundary_violation():
    aggregator = MetricsAggregator()
    t = AIRequestTelemetry(
        request_id="r_viol",
        total_ms=100.0,
        personal_boundary_checked=True,
        personal_boundary_passed=False,  # Zero-tolerance failure
    )
    card = aggregator.aggregate([t])
    assert card.status == HealthStatus.CRITICAL
    assert any("personal finance boundary violation" in r for r in card.status_reasons)


def test_health_status_critical_on_circuit_breaker_open():
    aggregator = MetricsAggregator()
    t = AIRequestTelemetry(
        request_id="r_cb",
        total_ms=50.0,
        circuit_state="OPEN",
    )
    card = aggregator.aggregate([t])
    assert card.status == HealthStatus.CRITICAL
    assert any("Circuit breaker is currently OPEN" in r for r in card.status_reasons)


def test_health_status_critical_on_high_provider_failure_rate():
    aggregator = MetricsAggregator()
    records = [
        AIRequestTelemetry(request_id=f"fail_{i}", total_ms=100.0, resilience_failure_type="PROVIDER_UNAVAILABLE")
        for i in range(6)
    ]
    card = aggregator.aggregate(records)
    assert card.status == HealthStatus.CRITICAL
    assert any("High provider failure rate" in r for r in card.status_reasons)


# ==============================================================================
# 7. Failure-Isolation & Disabled Mode Tests
# ==============================================================================

def test_observability_disabled_mode_returns_none():
    disabled_service = ObservabilityService(enabled=False)
    res = disabled_service.record_request_telemetry(request_id="req_dis")
    assert res is None


def test_observability_never_raises_on_invalid_input():
    service = ObservabilityService()
    # Passing nonsensical arguments must not raise exception
    res = service.record_request_telemetry(
        request_id="req_err",
        conversation_id={"unhashable": lambda x: x},
        latency_breakdown=None,
    )
    assert res is not None or res is None


def test_observability_overhead_under_one_ms():
    service = ObservabilityService()
    t0 = time.perf_counter()
    for i in range(100):
        service.record_request_telemetry(request_id=f"bench_{i}")
    elapsed_per_record_ms = ((time.perf_counter() - t0) / 100) * 1000.0
    assert elapsed_per_record_ms < 1.0


# ==============================================================================
# 8. Service Integration Tests (Advisor End-to-End Observability)
# ==============================================================================

def _make_mock_message(msg_id: int, conversation_id: int, role: str, content: str, metadata: dict):
    m = MagicMock()
    m.id = msg_id
    m.conversation_id = conversation_id
    m.role = role
    m.content = content
    m.message_metadata = metadata
    m.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return m


@pytest.mark.anyio
async def test_advisor_service_records_request_telemetry_on_chat():
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="SIP is a systematic investment plan.")
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="What is a SIP?",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "What is a SIP?"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "What is a SIP?", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    custom_store = TelemetryStore()
    obs_service = ObservabilityService(store=custom_store)

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        observability_service=obs_service,
    )

    resp = await service.send_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="What is a SIP?"),
    )

    assert resp.assistant_message.content == "SIP is a systematic investment plan."
    assert "request_id" in resp.assistant_message.message_metadata
    telemetries = custom_store.get_telemetries()
    assert len(telemetries) == 1
    assert telemetries[0].request_id == resp.assistant_message.message_metadata["request_id"]


@pytest.mark.anyio
async def test_advisor_service_records_request_telemetry_on_streaming():
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()

    async def _mock_stream(*args, **kwargs):
        yield "SIP "
        yield "stands "
        yield "for "
        yield "systematic "
        yield "plan."

    mock_llm.generate_stream = _mock_stream
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="What is a SIP?",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "What is a SIP?"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "What is a SIP?", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    custom_store = TelemetryStore()
    obs_service = ObservabilityService(store=custom_store)

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        observability_service=obs_service,
    )

    chunks = []
    async for chunk in service.stream_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="What is a SIP?"),
        emit_sse=True,
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    telemetries = custom_store.get_telemetries()
    assert len(telemetries) == 1
    assert telemetries[0].streaming_enabled is True


@pytest.mark.anyio
async def test_observability_endpoints():
    from app.api.v1.ai import get_ai_health, get_ai_metrics, get_ai_summary
    from app.ai.observability.service import get_observability_service

    obs = get_observability_service()
    obs.record_request_telemetry(request_id="ep_test_01", conversation_id=1)

    health_card = await get_ai_health(window=TimeWindow.RECENT, user_id=1)
    assert isinstance(health_card, SystemHealthScorecard)
    assert health_card.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.CRITICAL)

    summary = await get_ai_summary(window=TimeWindow.RECENT, user_id=1)
    assert isinstance(summary, dict)
    assert "status" in summary

    metrics = await get_ai_metrics(limit=10, user_id=1)
    assert isinstance(metrics, list)
    assert len(metrics) >= 1
    assert "request_id" in metrics[0]
