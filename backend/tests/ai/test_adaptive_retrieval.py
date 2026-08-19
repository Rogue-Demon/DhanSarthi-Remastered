"""
Phase L.6 Intelligent Retrieval Fusion & Adaptive Routing Test Suite.

Tests adaptive router deterministic rules, strategy selection, candidate bounds,
RRF parameters, fallback handling, authority/temporal protection, citation preservation,
and regression safety across Phases L.1 to L.5.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.adaptive_router import AdaptiveRetrievalRouter
from app.ai.rag.faiss_store import FAISSVectorStore
from app.ai.rag.ingestion import KnowledgeIngestionService
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    ComparisonInfo,
    OperationType,
    PersonalizationLevel,
    QueryExecutionPlan,
    QueryScope,
)
from app.ai.schemas.query_understanding import QueryUnderstanding
from app.ai.schemas.retrieval_strategy import (
    RetrievalExecutionPlan,
    RetrievalStrategy,
    SemanticStrategy,
)
from app.ai.semantic.minilm import MiniLMSemanticService
from app.core.config import settings
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


@pytest.fixture
def mock_embedding():
    return MockEmbeddingProvider(dim=384)


@pytest.fixture
def router():
    return AdaptiveRetrievalRouter()


# ---------------------------------------------------------------------------
# Router Deterministic Rule Tests (Scenarios 1-11)
# ---------------------------------------------------------------------------

def test_casual_query_routes_to_none(router):
    plan = QueryExecutionPlan(
        original_query="Hello DhanSarthi",
        intent=QueryIntent.CASUAL,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.CASUAL,
        operation=OperationType.EXPLAIN,
    )
    result = router.route(execution_plan=plan, retrieval_query="Hello DhanSarthi")
    assert result.strategy == RetrievalStrategy.NONE
    assert result.semantic_strategy == SemanticStrategy.NONE
    assert result.reason == "casual_query_bypass"


def test_greeting_routes_to_none(router):
    plan = QueryExecutionPlan(
        original_query="good morning",
        intent=QueryIntent.CASUAL,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.CASUAL,
        operation=OperationType.EXPLAIN,
    )
    result = router.route(execution_plan=plan, retrieval_query="good morning")
    assert result.strategy == RetrievalStrategy.NONE
    assert result.reason == "casual_query_bypass"


def test_capability_routes_to_none(router):
    plan = QueryExecutionPlan(
        original_query="what can you do?",
        intent=QueryIntent.CASUAL,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.CASUAL,
        operation=OperationType.EXPLAIN,
    )
    result = router.route(execution_plan=plan, retrieval_query="what can you do?")
    assert result.strategy == RetrievalStrategy.NONE
    assert result.reason == "casual_query_bypass"


def test_ambiguous_query_routes_to_none(router):
    plan = QueryExecutionPlan(
        original_query="invest",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.AMBIGUOUS,
        operation=OperationType.EXPLAIN,
        clarification_required=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="invest")
    assert result.strategy == RetrievalStrategy.NONE
    assert result.reason == "ambiguous_clarification_required"


def test_personal_finance_routes_to_none(router):
    plan = QueryExecutionPlan(
        original_query="How much did I spend this month?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.SPENDING_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_financial_engine=True,
        requires_rag=False,
    )
    result = router.route(execution_plan=plan, retrieval_query="How much did I spend this month?")
    assert result.strategy == RetrievalStrategy.NONE
    assert result.reason == "personal_finance_engine_only"


def test_general_finance_routes_to_hybrid(router):
    plan = QueryExecutionPlan(
        original_query="What is Public Provident Fund?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.EXPLAIN,
        requires_rag=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="What is Public Provident Fund?")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.semantic_strategy == SemanticStrategy.MINILM
    assert result.pgvector_top_k == 15
    assert result.faiss_top_k == 15


def test_mixed_query_routes_to_hybrid(router):
    plan = QueryExecutionPlan(
        original_query="Is my savings rate good for SIP investing?",
        intent=QueryIntent.MIXED,
        sub_intent=SubIntent.FINANCIAL_PLANNING,
        scope=QueryScope.MIXED,
        operation=OperationType.ANALYZE,
        requires_rag=True,
        requires_financial_engine=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="Is my savings rate good for SIP investing?")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.semantic_strategy == SemanticStrategy.MINILM
    assert result.pgvector_top_k == 20


def test_comparison_query_routes_to_hybrid_with_expanded_bounds(router):
    plan = QueryExecutionPlan(
        original_query="SIP vs Fixed Deposit",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.COMPARISON,
        operation=OperationType.COMPARE,
        comparison_info=ComparisonInfo(is_comparison=True, comparison_items=["SIP", "Fixed Deposit"]),
        requires_rag=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="SIP vs Fixed Deposit")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.semantic_strategy == SemanticStrategy.MINILM
    assert result.pgvector_top_k == 25
    assert result.faiss_top_k == 25
    assert result.rrf_k == 40
    assert result.reason == "comparison_query"


def test_authority_sensitive_query_routes_to_hybrid(router):
    plan = QueryExecutionPlan(
        original_query="RBI master circular on loan EMIs",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.LOOKUP,
        requires_rag=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="RBI master circular on loan EMIs")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.pgvector_top_k == 25
    assert result.rrf_k == 50
    assert result.reason == "authority_sensitive"


def test_historical_query_routes_to_hybrid(router):
    plan = QueryExecutionPlan(
        original_query="Income tax slabs FY 2024-25",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.LOOKUP,
        requires_rag=True,
    )
    result = router.route(execution_plan=plan, retrieval_query="Income tax slabs FY 2024-25")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.pgvector_top_k == 25
    assert result.reason == "authority_sensitive"  # "income tax" triggers authority sensitive rule


from app.ai.schemas.query_execution_plan import ExtractedEntity, EntityCategory

def test_short_financial_entity_routes_to_hybrid(router):
    sample_entity = ExtractedEntity(
        entity_type=EntityCategory.INVESTMENT_PRODUCT,
        value="SIP",
        raw_text="SIP",
    )
    understanding = QueryUnderstanding(
        original_query="SIP?",
        normalized_query="sip",
        corrected_query="sip",
        resolved_query="What is Systematic Investment Plan (SIP)?",
        retrieval_query="Systematic Investment Plan SIP mutual funds",
        entities=[sample_entity],
        intent=QueryIntent.GENERAL_FINANCE,
    )
    plan = QueryExecutionPlan(
        original_query="SIP?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.EXPLAIN,
        entities=[sample_entity],
        requires_rag=True,
    )
    result = router.route(query_understanding=understanding, execution_plan=plan, retrieval_query="SIP?")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.pgvector_top_k == 15


# ---------------------------------------------------------------------------
# Fallback & Resilience Tests (Scenarios 12-15)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pgvector_only_fallback(db_session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    await ingestion.ingest_document(
        title="RBI Capital Adequacy Rules",
        content_or_filepath="RBI specifies commercial banks must maintain minimum capital adequacy ratio of 9 percent.",
        source="Reserve Bank of India",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
    )

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)
    plan = RetrievalExecutionPlan(
        strategy=RetrievalStrategy.PGVECTOR_ONLY,
        semantic_strategy=SemanticStrategy.NONE,
    )

    docs = await retriever.retrieve("RBI capital adequacy ratio", retrieval_plan=plan)
    assert len(docs) > 0
    assert docs[0].metadata["retrieval_summary"]["retrieval_strategy"] == "PGVECTOR_ONLY"
    assert docs[0].metadata["retrieval_summary"]["faiss_used"] is False


@pytest.mark.anyio
async def test_faiss_failure_fallback(db_session, mock_embedding, monkeypatch):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    await ingestion.ingest_document(
        title="SEBI Mutual Fund Rules",
        content_or_filepath="SEBI regulates mutual fund scheme categorization.",
        source="SEBI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.SEBI,
    )

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    # Force FAISS search error
    def raise_faiss_err(*args, **kwargs):
        raise RuntimeError("FAISS index hardware error")

    if retriever._faiss_store._index is not None:
        monkeypatch.setattr(retriever._faiss_store, "search", raise_faiss_err)

    plan = RetrievalExecutionPlan(strategy=RetrievalStrategy.HYBRID)
    docs = await retriever.retrieve("SEBI mutual fund regulations", retrieval_plan=plan)

    assert len(docs) > 0
    assert docs[0].metadata["retrieval_summary"]["faiss_fallback"] is True


@pytest.mark.anyio
async def test_minilm_failure_fallback(db_session, mock_embedding, monkeypatch):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    await ingestion.ingest_document(
        title="Income Tax Chapter VI-A",
        content_or_filepath="Section 80C provides tax deduction up to 1.5 lakh rupees.",
        source="Income Tax Dept",
        category=KnowledgeCategory.TAXATION,
        authority=KnowledgeAuthority.INCOME_TAX,
    )

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    def raise_minilm_err(*args, **kwargs):
        raise RuntimeError("MiniLM OOM error")

    monkeypatch.setattr(retriever._minilm_service, "similarity_to_candidates", raise_minilm_err)

    plan = RetrievalExecutionPlan(strategy=RetrievalStrategy.HYBRID, semantic_strategy=SemanticStrategy.MINILM)
    docs = await retriever.retrieve("Section 80C deduction limit", retrieval_plan=plan)

    assert len(docs) > 0
    assert docs[0].metadata["retrieval_summary"]["minilm_used"] is False


@pytest.mark.anyio
async def test_both_retrieval_failure_returns_empty(db_session, mock_embedding, monkeypatch):
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    def raise_db_err(*args, **kwargs):
        raise RuntimeError("DB connection pool lost")

    def raise_faiss_err(*args, **kwargs):
        raise RuntimeError("FAISS search error")

    monkeypatch.setattr(retriever._chunk_repo, "search_similarity", raise_db_err)
    if retriever._faiss_store._index is not None:
        monkeypatch.setattr(retriever._faiss_store, "search", raise_faiss_err)

    plan = RetrievalExecutionPlan(strategy=RetrievalStrategy.HYBRID)
    docs = await retriever.retrieve("PPF interest rate", retrieval_plan=plan)

    assert docs == []


# ---------------------------------------------------------------------------
# Fusion, Authority & Temporal Protection (Scenarios 16-20)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_candidate_fusion_and_rrf_ranking(db_session, mock_embedding):
    doc = KnowledgeDocument(
        title="Fusion Test Doc",
        source="RBI",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
        country="India",
        jurisdiction="India",
        status=KnowledgeDocumentStatus.ACTIVE,
    )
    db_session.add(doc)
    db_session.commit()

    chunk1 = KnowledgeChunk(document_id=doc.id, chunk_index=0, content="Chunk A", embedding=[0.1]*384)
    chunk2 = KnowledgeChunk(document_id=doc.id, chunk_index=1, content="Chunk B", embedding=[0.2]*384)
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    pgvector_matches = [(chunk1, 0.90)]
    faiss_results = [{"chunk_id": str(chunk1.id), "distance": 0.1, "similarity_score": 0.88, "faiss_rank": 1}]

    fused, meta = retriever._fuse_candidates(pgvector_matches, faiss_results, candidate_limit=5, rrf_k=40)
    assert meta["fused_count"] == 1
    assert fused[0][0]._retrieval_source == "both"


@pytest.mark.anyio
async def test_authority_protection_preserved(db_session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)

    # Ingest Official RBI Doc
    await ingestion.ingest_document(
        title="RBI Master Circular on Banking",
        content_or_filepath="Official RBI Banking directives.",
        source="RBI",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
    )

    # Ingest General Unofficial Doc
    await ingestion.ingest_document(
        title="Blog Post on Banking",
        content_or_filepath="General unofficial thoughts on banking.",
        source="Personal Blog",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.GENERAL,
    )

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)
    plan = RetrievalExecutionPlan(strategy=RetrievalStrategy.HYBRID)

    docs = await retriever.retrieve("RBI banking circular", retrieval_plan=plan)
    assert len(docs) > 0
    # Top doc must be RBI authority doc due to Phase J reranker authority boosting
    assert docs[0].metadata["authority"] == KnowledgeAuthority.RBI


# ---------------------------------------------------------------------------
# Isolation, Config & Performance Tests (Scenarios 21-29)
# ---------------------------------------------------------------------------

def test_router_performance_latency(router):
    plan = QueryExecutionPlan(
        original_query="What is compound interest?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.EXPLAIN,
    )

    start = time.monotonic()
    for _ in range(500):
        _ = router.route(execution_plan=plan, retrieval_query="What is compound interest?")
    elapsed_ms = (time.monotonic() - start) * 1000
    avg_ms = elapsed_ms / 500

    # Routing overhead must be < 1.0 ms
    assert avg_ms < 1.0


def test_configuration_disabled_mode(router, monkeypatch):
    monkeypatch.setattr(settings, "adaptive_retrieval_enabled", False)

    plan = QueryExecutionPlan(
        original_query="Hello",
        intent=QueryIntent.CASUAL,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.CASUAL,
        operation=OperationType.EXPLAIN,
    )

    result = router.route(execution_plan=plan, retrieval_query="Hello")
    assert result.strategy == RetrievalStrategy.HYBRID
    assert result.reason == "adaptive_disabled_fallback"
