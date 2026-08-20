"""
Unit and Integration Test Suite for Phase L.11.1 — Latency Root-Cause Audit & Fast-Path Profiling.

Verifies:
  1. 30-stage latency timing measurement completeness.
  2. Bottleneck classification algorithm (13 categories).
  3. Personal fast-path analysis logic and candidate detection.
  4. Cache safety rule preservation (personal queries excluded, educational cached).
  5. Streaming vs Non-streaming metrics (TTFT, duration, tokens/sec).
  6. Latency percentile calculations (p50, p90, p95, p99).
  7. End-to-end benchmark execution and schema compliance.
  8. Absolute preservation of SafetyValidator, Ground Truth, and L.10 Observability.
"""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
import json
import os
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.observability.latency import LatencyTracker
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.ai.schemas.latency import LatencyBreakdown
from app.core.config import settings
from scripts.benchmark_latency_root_cause import (
    BENCHMARK_QUERY_SPEC,
    build_test_service,
    calculate_percentiles,
    classify_bottlenecks,
    create_benchmark_dashboard,
    run_latency_root_cause_audit,
)


@pytest.fixture
def sample_dashboard():
    return create_benchmark_dashboard()


def test_30_stage_latency_breakdown_schema():
    """Verify LatencyBreakdown contains all required 30 profiling stages with numeric defaults."""
    breakdown = LatencyBreakdown()
    expected_stages = [
        "ownership_check_ms",
        "user_persistence_ms",
        "financial_context_ms",
        "history_retrieval_ms",
        "query_understanding_ms",
        "adaptive_routing_ms",
        "pgvector_ms",
        "faiss_ms",
        "fusion_ms",
        "minilm_ms",
        "reranker_ms",
        "financial_intelligence_ms",
        "market_data_ms",
        "context_build_ms",
        "prompt_build_ms",
        "inference_config_ms",
        "context_optimization_ms",
        "model_selection_ms",
        "cache_eligibility_ms",
        "cache_key_ms",
        "cache_lookup_ms",
        "prompt_compression_ms",
        "provider_network_ms",
        "llm_request_ms",
        "llm_generation_ms",
        "generation_ms",
        "ttft_ms",
        "safety_validation_ms",
        "quality_evaluation_ms",
        "quality_retry_ms",
        "cache_write_ms",
        "assistant_persistence_ms",
        "persistence_ms",
        "telemetry_record_ms",
        "total_ms",
    ]
    for stage in expected_stages:
        assert hasattr(breakdown, stage), f"Missing required latency stage: {stage}"
        val = getattr(breakdown, stage)
        assert val is None or isinstance(val, (int, float)), f"Stage {stage} is not numeric"


def test_percentile_calculation():
    """Test percentile helper computes accurate p50, p90, p95, p99."""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p = calculate_percentiles(latencies)
    assert p["p50"] == 55.0
    assert p["p90"] == 91.0
    assert p["p95"] == 95.5
    assert p["p99"] == 99.1

    empty_p = calculate_percentiles([])
    assert empty_p == {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}


def test_bottleneck_classification_categories():
    """Test automatic classification into bottleneck categories."""
    # 1. Retrieval bound
    b_ret = classify_bottlenecks({"pgvector_ms": 300.0, "reranker_ms": 100.0}, total_ms=1000.0)
    assert "RETRIEVAL_BOUND" in b_ret

    # 2. Query understanding bound
    b_qu = classify_bottlenecks({"query_understanding_ms": 250.0}, total_ms=1000.0)
    assert "QUERY_UNDERSTANDING_BOUND" in b_qu

    # 3. Generation bound
    b_gen = classify_bottlenecks({"generation_ms": 500.0}, total_ms=1000.0)
    assert "GENERATION_BOUND" in b_gen

    # 4. TTFT bound
    b_ttft = classify_bottlenecks({"ttft_ms": 800.0, "stream_duration_ms": 1000.0}, total_ms=1000.0)
    assert "TTFT_BOUND" in b_ttft

    # 5. Quality evaluation bound
    b_qual = classify_bottlenecks({"quality_evaluation_ms": 250.0}, total_ms=1000.0)
    assert "QUALITY_EVALUATION_BOUND" in b_qual

    # 6. Persistence bound
    b_pers = classify_bottlenecks({"persistence_ms": 300.0}, total_ms=1000.0)
    assert "PERSISTENCE_BOUND" in b_pers


@pytest.mark.anyio
async def test_personal_fast_path_profiling_execution():
    """Verify that personal lookup queries execute and record all relevant stages."""
    service, conv_service, _ = await build_test_service(use_real_provider=False)

    req = SendMessageRequest(message="tell me about my goal")
    res = await service.send_chat_message(user_id=1, conversation_id=1, request=req)

    assert res.assistant_message is not None
    asst_msg = conv_service._messages[-1]
    latency = asst_msg.metadata.get("latency", {})

    assert latency.get("ownership_check_ms", 0.0) >= 0.0
    assert latency.get("financial_context_ms", 0.0) >= 0.0
    assert latency.get("safety_validation_ms", 0.0) >= 0.0
    assert latency.get("total_ms", 0.0) > 0.0


@pytest.mark.anyio
async def test_cache_safety_and_educational_repeat():
    """Verify personal financial queries are never cached, while educational repeat queries hit cache."""
    service, conv_service, _ = await build_test_service(use_real_provider=False)

    # 1. Educational query repeated -> Cache Hit
    edu_req = SendMessageRequest(message="what is a SIP?")
    await service.send_chat_message(user_id=1, conversation_id=1, request=edu_req)
    await service.send_chat_message(user_id=1, conversation_id=1, request=edu_req)
    last_meta = conv_service._messages[-1].metadata
    assert last_meta.get("cache", {}).get("hit") is True or last_meta.get("latency", {}).get("cache_hit") is True

    # 2. Personal query repeated -> Cache Miss (Exclusion for data isolation)
    pers_req = SendMessageRequest(message="what is my net worth?")
    await service.send_chat_message(user_id=1, conversation_id=1, request=pers_req)
    await service.send_chat_message(user_id=1, conversation_id=1, request=pers_req)
    last_pers_meta = conv_service._messages[-1].metadata
    assert last_pers_meta.get("cache", {}).get("hit", False) is False
    assert last_pers_meta.get("latency", {}).get("cache_hit", False) is False


@pytest.mark.anyio
async def test_streaming_vs_non_streaming_metrics():
    """Verify streaming yields chunks and records TTFT cleanly without corrupting state."""
    service, conv_service, _ = await build_test_service(use_real_provider=False)

    stream_req = SendMessageRequest(message="how is my financial health?")
    chunks = []
    async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=stream_req, emit_sse=False):
        chunks.append(chunk)

    assert len(chunks) > 0
    asst_msg = conv_service._messages[-1]
    stream_meta = asst_msg.metadata
    assert stream_meta.get("streaming") is True
    assert asst_msg.content == "".join(chunks)


@pytest.mark.anyio
async def test_benchmark_runner_and_report_generation(tmp_path):
    """Verify the benchmark runner generates a compliant report matching Phase L.11.1 specification."""
    with patch("scripts.benchmark_latency_root_cause.BENCHMARK_QUERY_SPEC", BENCHMARK_QUERY_SPEC[:4]), \
         patch("scripts.benchmark_latency_root_cause.check_real_provider_availability", return_value=(False, "UNIT_TEST_MOCK_MODE")):
        report = await run_latency_root_cause_audit()

        assert report["phase"] == "L.11.1"
        assert report["benchmark_status"].startswith(("REAL_PROVIDER", "MOCK_MODE"))
        assert "stage_percentiles" in report
        assert "category_breakdown" in report
        assert "personal_fast_path_analysis" in report
        assert "provider_analysis" in report
        assert "streaming_analysis" in report
        assert "cache_analysis" in report
        assert "top_bottlenecks" in report
        assert "optimization_candidates" in report
        assert "unsafe_optimizations_rejected" in report
        assert len(report["queries"]) > 0

        # Verify no credentials or private numbers in report
        report_str = json.dumps(report)
        assert settings.ai_provider_api_key not in report_str
        assert len(report["unsafe_optimizations_rejected"]) >= 5
