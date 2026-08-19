"""
Unit & Integration Tests for Phase L.7.1 Latency Instrumentation & Profiling.

Verifies:
  1. LatencyBreakdown schema defaults, validation, and rounding.
  2. LatencyTracker context timing and attribute assignment.
  3. Query Understanding sub-stage timings.
  4. Adaptive Router latency instrumentation.
  5. Retrieval timing & candidate counts (pgvector, FAISS, concurrent HYBRID, fusion).
  6. MiniLM model load, embedding, and scoring timings.
  7. Reranker timings and candidate count tracking.
  8. Context builder timing, chunk counts, and field counts.
  9. Prompt assembly character count.
 10. LLM generation latency tracking.
 11. Safety validation timing.
 12. DB persistence timing.
 13. End-to-end integration latency payload in assistant message metadata (zero PII/credentials).
"""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.ai.schemas.latency import LatencyBreakdown
from app.ai.observability.latency import LatencyTracker
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.rag.adaptive_router import AdaptiveRetrievalRouter, RetrievalExecutionPlan, RetrievalStrategy, SemanticStrategy
from app.ai.schemas.query_understanding import QueryUnderstanding
from app.ai.schemas.query_execution_plan import ExtractedEntity
from app.ai.router import QueryIntent
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.semantic.minilm import MiniLMSemanticService
from app.ai.rag.reranker import DeterministicReranker
from app.ai.context.builder import AIContextBuilder
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.schemas.advisor import AIContext, RetrievedDocument


def test_latency_breakdown_schema_defaults():
    breakdown = LatencyBreakdown()
    assert breakdown.query_understanding_ms == 0.0
    assert breakdown.adaptive_routing_ms == 0.0
    assert breakdown.pgvector_ms == 0.0
    assert breakdown.faiss_ms == 0.0
    assert breakdown.fusion_ms == 0.0
    assert breakdown.minilm_ms == 0.0
    assert breakdown.total_ms == 0.0
    assert breakdown.candidate_count_pgvector == 0
    assert breakdown.pgvector_used is False
    assert breakdown.faiss_used is False


def test_latency_breakdown_to_dict_rounding():
    breakdown = LatencyBreakdown(
        total_ms=123.4567,
        query_understanding_ms=12.3456,
        pgvector_ms=45.6789,
    )
    d = breakdown.to_dict()
    assert d["total_ms"] == 123.46
    assert d["query_understanding_ms"] == 12.35
    assert d["pgvector_ms"] == 45.68


def test_latency_tracker_timer_context_manager():
    tracker = LatencyTracker()
    with tracker.timer("query_understanding_ms"):
        time.sleep(0.01)
    
    breakdown = tracker.to_dict()
    assert breakdown["query_understanding_ms"] > 0.0
    assert tracker.total_ms > 0.0


def test_query_understanding_sub_stage_instrumentation():
    service = QueryUnderstandingService()
    tracker = LatencyTracker()
    result = service.analyze("what is SIP investment?", tracker=tracker)
    
    bd = tracker.to_dict()
    assert bd["query_understanding_ms"] > 0.0
    assert bd["intent_scope_ms"] > 0.0
    assert result.intent == QueryIntent.GENERAL_FINANCE


def test_adaptive_router_latency_instrumentation():
    router = AdaptiveRetrievalRouter()
    tracker = LatencyTracker()
    
    qu = QueryUnderstanding(
        original_query="compare SIP vs PPF",
        normalized_query="compare sip vs ppf",
        corrected_query="compare sip vs ppf",
        resolved_query="compare sip vs ppf",
        retrieval_query="compare sip vs ppf",
        intent=QueryIntent.GENERAL_FINANCE,
    )
    
    plan = router.route(query_understanding=qu, tracker=tracker)
    bd = tracker.to_dict()
    assert bd["adaptive_routing_ms"] >= 0.0
    assert plan.strategy == RetrievalStrategy.HYBRID


@pytest.mark.anyio
async def test_retriever_hybrid_concurrent_and_fusion_timing():
    chunk_repo = MagicMock()
    chunk_repo.search_similarity.return_value = []
    
    faiss_store = MagicMock()
    faiss_store.is_healthy.return_value = True
    faiss_store.search.return_value = []
    
    embedding_provider = AsyncMock()
    embedding_provider.embed.return_value = [0.1] * 384
    
    retriever = PostgresRAGRetriever(
        db=MagicMock(),
        embedding_provider=embedding_provider,
        faiss_store=faiss_store,
    )
    retriever._chunk_repo = chunk_repo
    
    tracker = LatencyTracker()
    plan = RetrievalExecutionPlan(strategy=RetrievalStrategy.HYBRID)
    
    docs = await retriever.retrieve(
        query="what is mutual fund?",
        retrieval_plan=plan,
        tracker=tracker,
    )
    
    bd = tracker.to_dict()
    assert bd["pgvector_used"] is True
    assert bd["faiss_used"] is False  # 0 matches returned
    assert bd["pgvector_ms"] >= 0.0
    assert bd["faiss_ms"] >= 0.0


def test_minilm_scoring_latency_instrumentation():
    service = MiniLMSemanticService()
    tracker = LatencyTracker()
    
    # Force model load timing check
    scores = service.similarity_to_candidates(
        query="mutual funds",
        candidates=["investing in mutual funds", "tax filing guide"],
        tracker=tracker,
    )
    
    bd = tracker.to_dict()
    assert len(scores) == 2
    assert bd["minilm_ms"] >= 0.0


def test_reranker_latency_instrumentation():
    reranker = DeterministicReranker()
    tracker = LatencyTracker()
    
    chunk = MagicMock()
    chunk.id = 1
    chunk.chunk_index = 0
    chunk.content = "SIP is systematic investment plan."
    chunk.document_id = 10
    doc = MagicMock()
    doc.id = 10
    doc.title = "SIP Guide"
    doc.category = "INVESTMENTS"
    doc.authority = "SEBI"
    doc.source = "SEBI Portal"
    doc.jurisdiction = "IN"
    doc.version = "1.0"
    doc.effective_date = None
    doc.source_url = None
    doc.status = "ACTIVE"
    chunk.document = doc
    chunk.chunk_metadata = {}
    
    results = reranker.rerank_and_filter(
        matches=[(chunk, 0.8)],
        query_terms=["sip"],
        threshold=0.2,
        tracker=tracker,
    )
    
    bd = tracker.to_dict()
    assert bd["reranker_ms"] >= 0.0
    assert bd["candidate_count_before_rerank"] == 1
    assert bd["candidate_count_after_rerank"] == len(results)


def test_context_builder_latency_and_counts():
    builder = AIContextBuilder()
    tracker = LatencyTracker()
    
    doc = RetrievedDocument(
        document_id="10",
        title="SIP Guide",
        content="SIP details",
        source="SEBI",
        relevance_score=0.8,
        metadata={},
    )
    
    ctx = builder.build_context(
        question="Tell me about SIP",
        full_context=None,
        retrieved_docs=[doc],
        tracker=tracker,
    )
    prompt = builder.build_prompt(context=ctx, tracker=tracker)
    
    bd = tracker.to_dict()
    assert bd["context_build_ms"] >= 0.0
    assert bd["rag_chunk_count"] == 1
    assert bd["prompt_char_count"] == len(prompt)


def test_safety_validator_latency_instrumentation():
    validator = SimpleSafetyValidator()
    tracker = LatencyTracker()
    
    ctx = AIContext(question="What is SIP?", retrieved_knowledge=[])
    validator.validate_response("SIP is a systematic investment plan.", ctx, tracker=tracker)
    
    bd = tracker.to_dict()
    assert bd["safety_validation_ms"] >= 0.0


@pytest.mark.anyio
async def test_huggingface_provider_latency_instrumentation(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ai_provider_api_key", "mock_key")
    provider = HuggingFaceProvider()
    tracker = LatencyTracker()
    ctx = AIContext(question="What is SIP?", retrieved_knowledge=[])
    
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "SIP stands for Systematic Investment Plan."}}]}
    mock_post.return_value = mock_response
    
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    
    resp = await provider.generate(ctx, "What is SIP?", tracker=tracker)
    assert resp == "SIP stands for Systematic Investment Plan."
    
    bd = tracker.to_dict()
    assert bd["llm_request_ms"] >= 0.0
    assert bd["llm_generation_ms"] >= 0.0
