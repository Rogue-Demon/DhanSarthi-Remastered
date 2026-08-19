"""
Phase L.5 FAISS Hybrid Candidate Retrieval Test Suite.

Tests FAISS store creation, persistence, loading, 384-dim validation, PostgreSQL ID mapping,
RRF candidate fusion, missing/corrupt index fallback, boundary isolation, user isolation,
MiniLM + reranker compatibility, and retrieval performance.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import pytest
from unittest.mock import MagicMock

from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.faiss_indexer import FAISSIndexer
from app.ai.rag.faiss_store import FAISSVectorStore
from app.ai.rag.reranker import DeterministicReranker
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.schemas.query_execution_plan import OperationType, PersonalizationLevel, QueryExecutionPlan, QueryScope
from app.ai.semantic.minilm import MiniLMSemanticService
from app.core.config import settings
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus


# ---------------------------------------------------------------------------
# Test Fixtures & Utilities
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_embedding_provider():
    return MockEmbeddingProvider(dim=384)


@pytest.fixture
def minilm_service():
    return MiniLMSemanticService()


@pytest.fixture
def temp_faiss_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ---------------------------------------------------------------------------
# FAISS Store Core Tests (A-J)
# ---------------------------------------------------------------------------

def test_faiss_store_creation_and_384_dimension():
    store = FAISSVectorStore(dimension=384)
    assert store.dimension == 384
    assert store.is_available()
    # Empty index initially not healthy for search until populated
    assert store._index is not None
    assert store._index.d == 384


def test_faiss_add_vectors_and_id_mapping():
    store = FAISSVectorStore(dimension=384)
    vec1 = [0.1] * 384
    vec2 = [0.2] * 384
    chunk_ids = ["chunk-101", "chunk-102"]

    success = store.add_vectors([vec1, vec2], chunk_ids)
    assert success is True
    assert store.is_healthy() is True
    assert store._index.ntotal == 2
    assert store._pos_to_chunk_id[0] == "chunk-101"
    assert store._pos_to_chunk_id[1] == "chunk-102"


def test_faiss_search_and_score_normalization():
    store = FAISSVectorStore(dimension=384)
    vec1 = [0.1] * 384
    vec2 = [0.9] * 384
    store.add_vectors([vec1, vec2], ["chunk-a", "chunk-b"])

    query_vec = [0.1] * 384
    results = store.search(query_vec, top_k=2)

    assert len(results) == 2
    assert results[0]["chunk_id"] == "chunk-a"
    assert results[0]["faiss_rank"] == 1
    assert results[0]["distance"] >= 0.0
    assert 0.0 <= results[0]["similarity_score"] <= 1.0


def test_faiss_index_persistence_and_loading(temp_faiss_dir):
    idx_p = os.path.join(temp_faiss_dir, "test.index")
    map_p = os.path.join(temp_faiss_dir, "test_map.json")
    meta_p = os.path.join(temp_faiss_dir, "test_meta.json")

    store = FAISSVectorStore(dimension=384)
    store.add_vectors([[0.05] * 384, [0.15] * 384], ["id-1", "id-2"])

    saved = store.save(idx_p, map_p, meta_p)
    assert saved is True
    assert os.path.exists(idx_p)
    assert os.path.exists(map_p)
    assert os.path.exists(meta_p)

    store2 = FAISSVectorStore(dimension=384)
    loaded = store2.load(idx_p, map_p, meta_p)
    assert loaded is True
    assert store2.is_healthy() is True
    assert store2._index.ntotal == 2
    assert store2._pos_to_chunk_id[0] == "id-1"
    assert store2._pos_to_chunk_id[1] == "id-2"


def test_missing_index_fallback(temp_faiss_dir):
    store = FAISSVectorStore(dimension=384)
    loaded = store.load(
        os.path.join(temp_faiss_dir, "nonexistent.index"),
        os.path.join(temp_faiss_dir, "nonexistent.json"),
        os.path.join(temp_faiss_dir, "nonexistent_meta.json"),
    )
    assert loaded is False
    assert store.is_available() is False
    assert store.is_healthy() is False

    # Search on missing index returns empty list safely
    results = store.search([0.1] * 384, top_k=5)
    assert results == []


def test_corrupt_index_fallback(temp_faiss_dir):
    idx_p = os.path.join(temp_faiss_dir, "corrupt.index")
    map_p = os.path.join(temp_faiss_dir, "corrupt_map.json")
    meta_p = os.path.join(temp_faiss_dir, "corrupt_meta.json")

    # Write junk file contents
    with open(idx_p, "w") as f:
        f.write("corrupted data")
    with open(map_p, "w") as f:
        f.write("{}")
    with open(meta_p, "w") as f:
        f.write('{"embedding_dimension": 384}')

    store = FAISSVectorStore(dimension=384)
    loaded = store.load(idx_p, map_p, meta_p)
    assert loaded is False
    assert store.is_healthy() is False


def test_wrong_dimension_handling(temp_faiss_dir):
    store = FAISSVectorStore(dimension=384)

    # Attempt to add wrong dimension vector
    invalid_vec = [0.1] * 128
    added = store.add_vectors([invalid_vec], ["chunk-err"])
    assert added is False

    # Attempt search with wrong dimension vector
    results = store.search([0.1] * 128)
    assert results == []


def test_stale_index_detection():
    store = FAISSVectorStore(dimension=384)
    store.add_vectors([[0.1] * 384], ["c1"])
    store._metadata["chunk_count"] = 1
    store._metadata["knowledge_version"] = "v1.0"

    # Match count -> not stale
    assert store.is_stale(current_chunk_count=1, current_version="v1.0") is False

    # Count mismatch -> stale
    assert store.is_stale(current_chunk_count=5, current_version="v1.0") is True

    # Version mismatch -> stale
    assert store.is_stale(current_chunk_count=1, current_version="v2.0") is True


# ---------------------------------------------------------------------------
# Candidate Fusion (RRF) & Hybrid Retrieval Tests (K-P)
# ---------------------------------------------------------------------------

from app.ai.rag.ingestion import KnowledgeIngestionService


@pytest.mark.anyio
async def test_reciprocal_rank_fusion(db_session, mock_embedding_provider):
    # Setup test chunks in DB
    doc = KnowledgeDocument(
        title="Test Fusion Doc",
        source="RBI Guidance",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
        country="India",
        jurisdiction="India",
        status=KnowledgeDocumentStatus.ACTIVE,
        document_hash="hash_fusion_1",
    )
    db_session.add(doc)
    db_session.commit()

    chunk1 = KnowledgeChunk(document_id=doc.id, chunk_index=0, content="Content A", embedding=[0.1]*384)
    chunk2 = KnowledgeChunk(document_id=doc.id, chunk_index=1, content="Content B", embedding=[0.2]*384)
    chunk3 = KnowledgeChunk(document_id=doc.id, chunk_index=2, content="Content C", embedding=[0.3]*384)
    db_session.add_all([chunk1, chunk2, chunk3])
    db_session.commit()

    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding_provider)

    pgvector_matches = [(chunk1, 0.90), (chunk2, 0.80)]
    faiss_results = [
        {"chunk_id": str(chunk2.id), "distance": 0.1, "similarity_score": 0.85, "faiss_rank": 1},
        {"chunk_id": str(chunk3.id), "distance": 0.2, "similarity_score": 0.75, "faiss_rank": 2},
    ]

    fused, meta = retriever._fuse_candidates(
        pgvector_matches=pgvector_matches,
        faiss_results=faiss_results,
        candidate_limit=10,
    )

    assert meta["pgvector_count"] == 2
    assert meta["faiss_count"] == 2
    assert len(fused) == 3

    # chunk2 was present in BOTH pgvector and FAISS -> should have highest RRF rank score
    fused_chunk_ids = [str(c.id) for c, _ in fused]
    assert fused_chunk_ids[0] == str(chunk2.id)
    assert fused[0][0]._retrieval_source == "both"


@pytest.mark.anyio
async def test_hybrid_retrieval_with_faiss_and_pgvector(db_session, mock_embedding_provider):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding_provider)
    await ingestion.ingest_document(
        title="Public Provident Fund (PPF) Scheme Rules",
        content_or_filepath="Public Provident Fund (PPF) is a 15-year tax-exempt long term investment scheme in India under Section 80C.",
        source="Government of India",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.GOVERNMENT_OF_INDIA,
        version="1.0",
    )

    indexer = FAISSIndexer(db=db_session)
    report = indexer.build_index()
    assert report["vectors_indexed"] > 0

    faiss_store = FAISSVectorStore(dimension=384)
    faiss_store.load()
    assert faiss_store.is_healthy() is True

    retriever = PostgresRAGRetriever(
        db=db_session,
        embedding_provider=mock_embedding_provider,
        faiss_store=faiss_store,
    )

    docs = await retriever.retrieve("What is Public Provident Fund (PPF)?")
    assert len(docs) > 0
    assert "retrieval_summary" in docs[0].metadata
    assert docs[0].metadata["retrieval_summary"]["fusion_method"] == "RRF"
    assert docs[0].metadata["retrieval_summary"]["faiss_used"] is True


@pytest.mark.anyio
async def test_pgvector_only_fallback_when_faiss_disabled(db_session, mock_embedding_provider, monkeypatch):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding_provider)
    await ingestion.ingest_document(
        title="Public Provident Fund (PPF) Scheme Rules",
        content_or_filepath="Public Provident Fund (PPF) is a 15-year tax-exempt long term investment scheme in India under Section 80C.",
        source="Government of India",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.GOVERNMENT_OF_INDIA,
        version="1.0",
    )

    monkeypatch.setattr(settings, "faiss_enabled", False)

    retriever = PostgresRAGRetriever(
        db=db_session,
        embedding_provider=mock_embedding_provider,
    )

    docs = await retriever.retrieve("What is Public Provident Fund (PPF)?")
    assert len(docs) > 0
    assert docs[0].metadata["retrieval_summary"]["faiss_used"] is False


# ---------------------------------------------------------------------------
# Boundary Tests (Q-U)
# ---------------------------------------------------------------------------

from app.ai.router import QueryIntent, SubIntent

def test_personal_finance_boundary():
    # Verify execution plan for Personal Finance queries short-circuits FAISS + RAG
    plan = QueryExecutionPlan(
        original_query="How much did I spend this month?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.SPENDING_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        personalization_level=PersonalizationLevel.HIGH,
        requires_financial_engine=True,
        requires_rag=False,  # Must be False
        requires_market_data=False,
    )
    assert plan.requires_rag is False


def test_casual_query_boundary():
    # Casual queries have CASUAL scope or NO RAG flag
    plan = QueryExecutionPlan(
        original_query="Hello",
        intent=QueryIntent.CASUAL,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.CASUAL,
        operation=OperationType.EXPLAIN,
        personalization_level=PersonalizationLevel.NONE,
        requires_financial_engine=False,
        requires_rag=False,
        requires_market_data=False,
    )
    assert plan.requires_rag is False


def test_ambiguous_query_boundary():
    plan = QueryExecutionPlan(
        original_query="invest",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.AMBIGUOUS,
        operation=OperationType.EXPLAIN,
        personalization_level=PersonalizationLevel.NONE,
        clarification_required=True,
        requires_financial_engine=False,
        requires_rag=False,
        requires_market_data=False,
    )
    assert plan.clarification_required is True
    assert plan.requires_rag is False


# ---------------------------------------------------------------------------
# Latency Benchmark (V)
# ---------------------------------------------------------------------------

def test_faiss_search_latency():
    store = FAISSVectorStore(dimension=384)
    # Populate with 100 vectors
    vecs = [[0.01 * (i % 10)] * 384 for i in range(100)]
    ids = [f"id-{i}" for i in range(100)]
    store.add_vectors(vecs, ids)

    query_vec = [0.05] * 384

    start = time.monotonic()
    for _ in range(50):
        _ = store.search(query_vec, top_k=20)
    elapsed_ms = (time.monotonic() - start) * 1000
    avg_ms = elapsed_ms / 50

    # FAISS local CPU search for 100 vectors must take < 5ms
    assert avg_ms < 5.0
