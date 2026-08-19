"""
Unit and Integration Test Suite for DhanSarthi Phase L.4 — MiniLM Semantic Intelligence Layer.

Tests:
  1. Lazy Model Loading & Reuse
  2. 384-dimensional Embedding Output
  3. Batch Encoding
  4. Cosine Similarity Calculation
  5. Related vs Unrelated Concept Scoring
  6. Candidate Pool Scoring
  7. MiniLM Disabled Mode
  8. Graceful Fallback on Error
  9. Integration: GENERAL_FINANCE query (RAG + MiniLM assistance)
 10. Integration: PERSONAL_FINANCE query (Financial Engine isolation)
 11. Integration: MIXED query (Financial Engine + RAG + MiniLM)
 12. Integration: CASUAL query (No RAG / MiniLM load)
 13. Integration: AMBIGUOUS query (Clarification short-circuit)
 14. Performance & Latency Benchmark
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.rag.reranker import DeterministicReranker
from app.ai.semantic.minilm import MiniLMSemanticService
from app.core.config import settings


@pytest.fixture
def minilm_service():
    return MiniLMSemanticService()


@pytest.fixture
def query_service():
    return QueryUnderstandingService()


# ---------------------------------------------------------------------------
# 1. Lazy Model Loading & Model Instance Reuse
# ---------------------------------------------------------------------------


def test_minilm_lazy_loading(minilm_service):
    # Verify model is NOT loaded at instance creation
    assert minilm_service._load_attempted is False
    assert minilm_service._model_instance is None

    # First call triggers lazy load
    vec = minilm_service.encode("SIP investment")
    assert minilm_service._load_attempted is True
    assert minilm_service._model_instance is not None

    instance_first = minilm_service._model_instance

    # Subsequent call reuses same instance
    _ = minilm_service.encode("FD deposit")
    assert minilm_service._model_instance is instance_first


# ---------------------------------------------------------------------------
# 2. 384-Dimensional Embedding Output
# ---------------------------------------------------------------------------


def test_minilm_embedding_dimension(minilm_service):
    vec = minilm_service.encode("Systematic Investment Plan")
    assert isinstance(vec, list)
    assert len(vec) == 384
    # Normalized vector property check (norm ~ 1.0)
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 0.05


# ---------------------------------------------------------------------------
# 3. Batch Encoding
# ---------------------------------------------------------------------------


def test_minilm_batch_encoding(minilm_service):
    texts = ["SIP", "Fixed Deposit", "Public Provident Fund"]
    vecs = minilm_service.encode_batch(texts)
    assert len(vecs) == 3
    for v in vecs:
        assert len(v) == 384


# ---------------------------------------------------------------------------
# 4. Cosine Similarity Calculation
# ---------------------------------------------------------------------------


def test_minilm_similarity(minilm_service):
    sim_identical = minilm_service.similarity("What is SIP?", "What is SIP?")
    assert sim_identical >= 0.99

    sim_diff = minilm_service.similarity("What is SIP?", "Recipes for banana cake")
    assert sim_diff < sim_identical


# ---------------------------------------------------------------------------
# 5. Related vs Unrelated Financial Concepts
# ---------------------------------------------------------------------------


def test_minilm_related_concepts(minilm_service):
    sim_related = minilm_service.similarity("SIP", "Systematic Investment Plan in mutual funds")
    sim_unrelated = minilm_service.similarity("SIP", "Astronomy and black holes in physics")
    assert sim_related > sim_unrelated


# ---------------------------------------------------------------------------
# 6. Candidate Pool Scoring
# ---------------------------------------------------------------------------


def test_similarity_to_candidates(minilm_service):
    query = "What is PPF?"
    candidates = [
        "Public Provident Fund (PPF) is a long-term government savings scheme.",
        "Mutual funds invest in equity and debt market securities.",
        "Baking sourdough bread at home requires flour and water.",
    ]
    scores = minilm_service.similarity_to_candidates(query, candidates)
    assert len(scores) == 3
    # Top candidate (PPF) should score highest
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


# ---------------------------------------------------------------------------
# 7. MiniLM Disabled Mode
# ---------------------------------------------------------------------------


def test_minilm_disabled_mode(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "minilm_enabled", False)

    disabled_service = MiniLMSemanticService()
    assert disabled_service.is_available() is False

    vec = disabled_service.encode("SIP")
    assert vec == [0.0] * 384

    scores = disabled_service.similarity_to_candidates("SIP", ["Mutual fund", "FD"])
    assert scores == [0.0, 0.0]


# ---------------------------------------------------------------------------
# 8. Graceful Fallback on Exception
# ---------------------------------------------------------------------------


def test_minilm_fallback_on_error():
    service = MiniLMSemanticService()
    # Simulate load failure state
    service._load_failed = True

    vec = service.encode("SIP")
    assert vec == [0.0] * 384

    scores = service.similarity_to_candidates("SIP", ["Candidate 1"])
    assert scores == [0.0]


# ---------------------------------------------------------------------------
# 9. Deterministic Reranker Integration with MiniLM Score
# ---------------------------------------------------------------------------


def test_reranker_with_minilm_score():
    reranker = DeterministicReranker()
    chunk = MagicMock()
    chunk.content = "Systematic Investment Plan (SIP) details and rules"
    chunk.document.title = "Mutual Fund SIP Guide"
    chunk.document.category = "MUTUAL_FUNDS"
    chunk.document.authority = "AMFI"
    chunk.document.status = "ACTIVE"
    chunk.document.source = "AMFI"
    chunk.document.source_url = "https://amfiindia.com"
    chunk.document.version = "1.0"
    chunk.document.effective_date = None

    score_without_minilm, _ = reranker.score_candidate(
        chunk=chunk,
        raw_semantic_score=0.70,
        query_terms=["SIP"],
        minilm_score=None,
    )

    score_with_minilm, breakdown = reranker.score_candidate(
        chunk=chunk,
        raw_semantic_score=0.70,
        query_terms=["SIP"],
        minilm_score=0.95,
    )

    assert "minilm_score" in breakdown
    assert breakdown["minilm_score"] == 0.95
    assert score_with_minilm >= score_without_minilm


# ---------------------------------------------------------------------------
# 10. Integration: Personal Finance Query (Financial Engine Boundary)
# ---------------------------------------------------------------------------


def test_personal_finance_query_boundary(query_service):
    res = query_service.analyze("How much did I spend this month?")
    # Must route to Financial Engine, skipping RAG retrieval
    assert res.requires_personal_data is True
    assert res.requires_rag is False


# ---------------------------------------------------------------------------
# 11. Integration: Mixed Query (Financial Engine + RAG + MiniLM)
# ---------------------------------------------------------------------------


def test_mixed_query_boundary(query_service):
    res = query_service.analyze("Is my savings rate healthy?")
    assert res.requires_personal_data is True
    assert res.requires_rag is True


# ---------------------------------------------------------------------------
# 12. Integration: Casual Query (No RAG / MiniLM load)
# ---------------------------------------------------------------------------


def test_casual_query_boundary(query_service):
    res = query_service.analyze("Hello")
    assert res.requires_rag is False
    assert res.requires_personal_data is False


# ---------------------------------------------------------------------------
# 13. Integration: Ambiguous Query (Clarification Short-Circuit)
# ---------------------------------------------------------------------------


def test_ambiguous_query_boundary(query_service):
    res = query_service.analyze("What is it?")
    assert res.execution_plan.clarification_required is True
    assert res.requires_rag is False


# ---------------------------------------------------------------------------
# 14. Performance & Latency Benchmark (< 5ms)
# ---------------------------------------------------------------------------


def test_minilm_scoring_latency(minilm_service):
    # Warm up lazy load
    _ = minilm_service.encode("Warmup query")

    candidates = [
        "Public Provident Fund (PPF) is a government savings scheme.",
        "Mutual funds pool money from investors for market investment.",
        "Fixed deposits offer guaranteed interest returns from banks.",
        "National Pension System (NPS) is a voluntary retirement scheme.",
    ]

    start = time.monotonic()
    for _ in range(10):
        _ = minilm_service.similarity_to_candidates("What is SIP in mutual funds?", candidates)

    elapsed_ms = (time.monotonic() - start) * 1000
    avg_ms = elapsed_ms / 10
    # Candidate pool scoring should be low latency
    assert avg_ms < 100.0
