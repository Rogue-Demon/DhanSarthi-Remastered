"""
Unit/integration tests for PostgresRAGRetriever & KnowledgeChunkRepository — Phase 10.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.ingestion import KnowledgeIngestionService
from app.ai.rag.retriever import PostgresRAGRetriever
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


def _clean_rag(db: Session) -> None:
    db.query(KnowledgeChunk).delete()
    db.query(KnowledgeDocument).delete()
    db.commit()


class TestPostgresRAGRetriever:
    @pytest.mark.anyio
    async def test_vector_similarity_retrieval(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        ingest_svc = KnowledgeIngestionService(db_session, emb_provider)

        # Ingest test knowledge document
        await ingest_svc.ingest_document(
            title="Tax Deductions 2026",
            content_or_filepath="Details on Section 80C deductions for income tax filings in India.",
            source="Income Tax Department",
            category=KnowledgeCategory.TAX,
            country="IND",
            jurisdiction="India",
        )

        retriever = PostgresRAGRetriever(db_session, emb_provider, top_k=5)
        docs = await retriever.retrieve(query="What are Section 80C deductions?")

        assert len(docs) > 0
        assert docs[0].title == "Tax Deductions 2026"
        assert "Income Tax Department" in docs[0].source
        assert docs[0].relevance_score > 0.0

    @pytest.mark.anyio
    async def test_category_metadata_filtering(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        ingest_svc = KnowledgeIngestionService(db_session, emb_provider)

        # Ingest Tax document
        await ingest_svc.ingest_document(
            title="Tax Rules",
            content_or_filepath="Income tax calculation rules.",
            source="Tax Authority",
            category=KnowledgeCategory.TAX,
        )

        # Ingest Loan document
        await ingest_svc.ingest_document(
            title="Home Loan Rules",
            content_or_filepath="Home loan interest rates and EMI calculation rules.",
            source="RBI",
            category=KnowledgeCategory.LOAN,
        )

        retriever = PostgresRAGRetriever(db_session, emb_provider)

        # Filter strictly by category=TAX
        tax_docs = await retriever.retrieve(query="rules", filters={"category": KnowledgeCategory.TAX})
        assert all(d.metadata.get("category") == KnowledgeCategory.TAX for d in tax_docs)
        assert any(d.title == "Tax Rules" for d in tax_docs)
        assert not any(d.title == "Home Loan Rules" for d in tax_docs)

    @pytest.mark.anyio
    async def test_inactive_documents_are_not_retrieved(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        ingest_svc = KnowledgeIngestionService(db_session, emb_provider)

        res = await ingest_svc.ingest_document(
            title="Archived Rulebook",
            content_or_filepath="Archived tax policies from 2010.",
            source="Old Tax Authority",
        )

        # Mark document as ARCHIVED
        doc = db_session.get(KnowledgeDocument, res["document_id"])
        doc.status = KnowledgeDocumentStatus.ARCHIVED
        db_session.flush()

        retriever = PostgresRAGRetriever(db_session, emb_provider)
        results = await retriever.retrieve(query="Archived tax policies")

        assert not any(r.title == "Archived Rulebook" for r in results)

    @pytest.mark.anyio
    async def test_empty_query_returns_empty_list(self, db_session: Session):
        emb_provider = MockEmbeddingProvider()
        retriever = PostgresRAGRetriever(db_session, emb_provider)

        assert await retriever.retrieve(query="") == []
        assert await retriever.retrieve(query="   ") == []
