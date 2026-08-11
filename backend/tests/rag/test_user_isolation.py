"""
Security & User Isolation tests — Phase 10.

CRITICAL INVARIANT:
User personal financial data (Income, Expenses, Assets, Liabilities, Loans, Goals,
Transactions) must NEVER be inserted into global RAG tables (KnowledgeDocument / KnowledgeChunk).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.income import Income
from app.models.expense import Expense
from app.models.asset import Asset
from app.models.enums import IncomeFrequency, AssetType, Persona, RiskProfile
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.user import User
from app.models.profile import Profile
from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.ingestion import KnowledgeIngestionService

TODAY = date.today()


def _seed_user(db: Session, user_id: int) -> None:
    u = User(id=user_id, email=f"user_iso_{user_id}@example.com", password_hash="hash")
    db.add(u)
    p = Profile(
        user_id=user_id,
        display_name=f"User {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    )
    db.add(p)
    db.flush()


class TestRAGUserIsolation:
    def test_user_financial_records_do_not_populate_rag_tables(self, db_session: Session):
        """User personal transactions and assets must not exist in global RAG Knowledge tables."""
        # Clear any RAG documents seeded by previous tests in the shared session
        db_session.query(KnowledgeChunk).delete()
        db_session.query(KnowledgeDocument).delete()
        db_session.commit()

        _seed_user(db_session, 601)

        # Create private user financial records
        db_session.add(Income(
            user_id=601, source="Private Salary", amount=Decimal("150000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.add(Expense(
            user_id=601, category="RENT", amount=Decimal("40000"),
            expense_date=TODAY, description="Private Rent",
        ))
        db_session.add(Asset(
            user_id=601, name="Private Bank Account", asset_type=AssetType.BANK_BALANCE,
            value=Decimal("800000"), valuation_date=TODAY,
        ))
        db_session.flush()

        # Query global RAG knowledge tables
        rag_docs = db_session.query(KnowledgeDocument).all()
        rag_chunks = db_session.query(KnowledgeChunk).all()

        # Zero user records should exist in RAG tables
        assert len(rag_docs) == 0
        assert len(rag_chunks) == 0

        # Confirm user text/sources are not leaked into any RAG content
        for doc in rag_docs:
            assert "Private Salary" not in doc.title
            assert "Private Rent" not in doc.description
        for chunk in rag_chunks:
            assert "150000" not in chunk.content
            assert "Private Bank Account" not in chunk.content

    @pytest.mark.anyio
    async def test_global_rag_ingestion_has_no_user_id_fk(self, db_session: Session):
        """KnowledgeDocument and KnowledgeChunk tables must not have user_id foreign keys."""
        emb_provider = MockEmbeddingProvider()
        svc = KnowledgeIngestionService(db_session, emb_provider)

        res = await svc.ingest_document(
            title="General Taxation Rules",
            content_or_filepath="General tax guidance for all citizens.",
            source="Ministry of Finance",
        )

        doc = db_session.get(KnowledgeDocument, res["document_id"])
        chunk = doc.chunks[0]

        # Invariant check: Knowledge tables are global and do not contain user_id attributes
        assert not hasattr(doc, "user_id")
        assert not hasattr(chunk, "user_id")
