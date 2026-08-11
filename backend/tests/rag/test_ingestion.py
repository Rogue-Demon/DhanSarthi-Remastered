"""
Unit tests for KnowledgeIngestionService — Phase 10.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.ai.exceptions import AIConfigurationError
from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.ingestion import KnowledgeIngestionError, KnowledgeIngestionService
from app.models.enums import KnowledgeAuthority, KnowledgeCategory
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


def _clean_rag(db: Session) -> None:
    db.query(KnowledgeChunk).delete()
    db.query(KnowledgeDocument).delete()
    db.commit()


class TestKnowledgeIngestionService:
    @pytest.mark.anyio
    async def test_successful_document_ingestion(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        svc = KnowledgeIngestionService(db_session, emb_provider)

        res = await svc.ingest_document(
            title="RBI Housing Loan Guidelines 2026",
            content_or_filepath="Housing loan EMI calculation guidelines published by Reserve Bank of India.",
            source="Reserve Bank of India",
            category=KnowledgeCategory.LOAN,
            authority=KnowledgeAuthority.REGULATOR,
        )

        assert res["status"] == "success"
        assert res["chunk_count"] == 1
        assert "document_id" in res

        # Verify database records
        doc = db_session.get(KnowledgeDocument, res["document_id"])
        assert doc is not None
        assert doc.title == "RBI Housing Loan Guidelines 2026"
        assert doc.category == KnowledgeCategory.LOAN
        assert len(doc.chunks) == 1
        assert len(doc.chunks[0].embedding) == 384

    @pytest.mark.anyio
    async def test_duplicate_document_skipped(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        svc = KnowledgeIngestionService(db_session, emb_provider)

        content = "Systematic Investment Plan (SIP) benefits and rupee cost averaging rules."

        # First ingestion
        res1 = await svc.ingest_document(
            title="SIP Guide",
            content_or_filepath=content,
            source="AMFI",
        )
        assert res1["status"] == "success"

        # Duplicate ingestion of same content
        res2 = await svc.ingest_document(
            title="SIP Guide Duplicate",
            content_or_filepath=content,
            source="AMFI Duplicate",
        )
        assert res2["status"] == "duplicate_skipped"
        assert res2["document_id"] == res1["document_id"]

    @pytest.mark.anyio
    async def test_dry_run_mode_no_database_write(self, db_session: Session):
        _clean_rag(db_session)
        emb_provider = MockEmbeddingProvider()
        svc = KnowledgeIngestionService(db_session, emb_provider)

        res = await svc.ingest_document(
            title="Dry Run Test Document",
            content_or_filepath="Content for dry run ingestion testing.",
            source="Test Agency",
            dry_run=True,
        )

        assert res["status"] == "dry_run_success"
        assert db_session.query(KnowledgeDocument).count() == 0

    @pytest.mark.anyio
    async def test_empty_title_raises_ingestion_error(self, db_session: Session):
        emb_provider = MockEmbeddingProvider()
        svc = KnowledgeIngestionService(db_session, emb_provider)

        with pytest.raises(KnowledgeIngestionError) as exc:
            await svc.ingest_document(
                title="",
                content_or_filepath="Some text",
                source="Agency",
            )
        assert "title cannot be empty" in str(exc.value)

    @pytest.mark.anyio
    async def test_invalid_vector_dimension_raises_configuration_error(self, db_session: Session):
        class BadDimensionEmbeddingProvider(MockEmbeddingProvider):
            async def embed(self, text: str) -> list[float]:
                return [0.1, 0.2]  # Returns dim=2 instead of dim=384

        svc = KnowledgeIngestionService(db_session, BadDimensionEmbeddingProvider())

        with pytest.raises(AIConfigurationError) as exc:
            await svc.ingest_document(
                title="Bad Vector Doc",
                content_or_filepath="Test text content",
                source="Source",
            )
        assert "dimension" in str(exc.value)
