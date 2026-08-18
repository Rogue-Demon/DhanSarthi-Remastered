"""
Test suite for Phase J - RAG Retrieval Intelligence & Evaluation.

Verifies:
  1. Query normalization & Hinglish phrasing.
  2. Query expansion using dictionary.
  3. Historical intent detection.
  4. Exact terminology and synonym retrieval.
  5. Authority prioritization & topic scoring.
  6. Deduplication & context diversity.
  7. RAG abstention boundary.
"""

import pytest
from sqlalchemy.orm import Session

from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.ingestion import KnowledgeIngestionService
from app.ai.rag.query_processor import QueryProcessor
from app.ai.rag.reranker import DeterministicReranker
from app.ai.rag.retriever import PostgresRAGRetriever
from app.models.enums import KnowledgeAuthority, KnowledgeCategory
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


def test_query_processor_normalization():
    processor = QueryProcessor()

    _, norm1, _, _, _ = processor.process("SIP kya hai?")
    assert norm1 == "sip"

    _, norm2, _, _, _ = processor.process("MF kya hota hai?")
    assert norm2 == "mf"

    _, norm3, _, _, _ = processor.process("What are PPF rules and regulations???")
    assert "ppf" in norm3


def test_query_processor_expansion():
    processor = QueryProcessor()

    _, _, expanded_sip, _, _ = processor.process("SIP")
    assert "Systematic Investment Plan" in expanded_sip
    assert "mutual fund" in expanded_sip

    _, _, expanded_nav, _, _ = processor.process("NAV")
    assert "Net Asset Value" in expanded_nav

    _, _, expanded_tds, _, _ = processor.process("TDS")
    assert "Tax Deducted at Source" in expanded_tds


def test_historical_intent_detection():
    processor = QueryProcessor()

    _, _, _, is_hist1, tag1 = processor.process("What were the tax rules in FY 2024-25?")
    assert is_hist1 is True
    assert "2024" in tag1

    _, _, _, is_hist2, _ = processor.process("What are the current tax rules?")
    assert is_hist2 is False


@pytest.fixture
def mock_embedding():
    return MockEmbeddingProvider()


@pytest.mark.anyio
async def test_exact_terminology_retrieval(db_session: Session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    await ingestion.ingest_document(
        title="AMFI Systematic Facilities: SIP, Systematic Transfer Plan (STP), and SWP",
        content_or_filepath="A Systematic Investment Plan (SIP) allows investors to invest a fixed amount regularly in mutual funds.",
        source="AMFI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.AMFI,
    )
    await ingestion.ingest_document(
        title="SEBI Categorization and Rationalization of Mutual Fund Schemes",
        content_or_filepath="Mutual Funds (MF) in India are regulated by SEBI under 5 broad scheme categories.",
        source="SEBI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.SEBI,
    )

    docs_sip = await retriever.retrieve("SIP")
    assert len(docs_sip) > 0
    top_sip = docs_sip[0]
    assert "SIP" in top_sip.title or "Systematic Investment Plan" in top_sip.title

    docs_mf = await retriever.retrieve("MF kya hota hai?")
    assert len(docs_mf) > 0
    top_mf = docs_mf[0]
    assert "Mutual Fund" in top_mf.title or "AMFI" in top_mf.source or "SEBI" in top_mf.source


@pytest.mark.anyio
async def test_authority_priority(db_session: Session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    await ingestion.ingest_document(
        title="SEBI Riskometer Evaluation and Product Labeling Rules",
        content_or_filepath="Riskometer measures risk levels in mutual funds across 6 risk tiers.",
        source="SEBI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.SEBI,
    )
    await ingestion.ingest_document(
        title="RBI DICGC Bank Deposit Insurance Protection Scheme",
        content_or_filepath="DICGC protects bank deposits up to 5 Lakh rupees per bank depositor.",
        source="RBI",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
    )

    # Riskometer query should prioritize SEBI
    docs_riskometer = await retriever.retrieve("What is SEBI riskometer?")
    assert len(docs_riskometer) > 0
    top_auth = str(docs_riskometer[0].metadata.get("authority")).upper()
    assert "SEBI" in top_auth

    # DICGC query should prioritize RBI
    docs_dicgc = await retriever.retrieve("What is DICGC bank deposit insurance?")
    assert len(docs_dicgc) > 0
    top_rbi_auth = str(docs_dicgc[0].metadata.get("authority")).upper()
    assert "RBI" in top_rbi_auth


@pytest.mark.anyio
async def test_deduplication_and_diversity(db_session: Session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    await ingestion.ingest_document(
        title="AMFI Mutual Fund Rules Part 1",
        content_or_filepath="Mutual fund rules for investors part 1.",
        source="AMFI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.AMFI,
    )
    await ingestion.ingest_document(
        title="AMFI Mutual Fund Rules Part 2",
        content_or_filepath="Mutual fund rules for investors part 2.",
        source="AMFI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.AMFI,
    )

    docs = await retriever.retrieve("Mutual fund investment rules")
    assert len(docs) <= 5  # Respect top_k limit

    # Count occurrences of document_id to verify max 2 chunks per doc
    doc_counts = {}
    for doc in docs:
        doc_counts[doc.document_id] = doc_counts.get(doc.document_id, 0) + 1
        assert doc_counts[doc.document_id] <= 2


@pytest.mark.anyio
async def test_rag_abstention_boundary(db_session: Session, mock_embedding):
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding, similarity_threshold=0.85)

    # Completely unrelated query should abstain (return 0 docs)
    docs = await retriever.retrieve("What is the price of Martian cryptocurrency coin right now?")
    assert len(docs) == 0


@pytest.mark.anyio
async def test_comprehensive_rag_regression_scenarios(db_session: Session, mock_embedding):
    ingestion = KnowledgeIngestionService(db=db_session, embedding_provider=mock_embedding)
    retriever = PostgresRAGRetriever(db=db_session, embedding_provider=mock_embedding)

    await ingestion.ingest_document(
        title="AMFI Systematic Facilities: SIP, Systematic Transfer Plan (STP), and SWP",
        content_or_filepath="A Systematic Investment Plan (SIP) allows investors to invest a fixed amount regularly in mutual funds.",
        source="AMFI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.AMFI,
    )
    await ingestion.ingest_document(
        title="SEBI Riskometer Evaluation and Product Labeling Rules",
        content_or_filepath="Riskometer measures risk levels in mutual funds across 6 risk tiers.",
        source="SEBI",
        category=KnowledgeCategory.MUTUAL_FUNDS,
        authority=KnowledgeAuthority.SEBI,
    )
    await ingestion.ingest_document(
        title="PFRDA Master Regulations on NPS Tier I and Tier II Architecture",
        content_or_filepath="National Pension System (NPS) is regulated by PFRDA.",
        source="PFRDA",
        category=KnowledgeCategory.RETIREMENT,
        authority=KnowledgeAuthority.PFRDA,
    )
    await ingestion.ingest_document(
        title="Tax Deducted at Source (TDS) Provisions on Salary and Interest",
        content_or_filepath="TDS is regulated by the Income Tax Department.",
        source="Income Tax Department",
        category=KnowledgeCategory.TAXATION,
        authority=KnowledgeAuthority.INCOME_TAX,
    )
    await ingestion.ingest_document(
        title="RBI Master Direction on Know Your Customer (KYC) and Digital Banking",
        content_or_filepath="KYC regulations are governed by RBI.",
        source="RBI",
        category=KnowledgeCategory.BANKING,
        authority=KnowledgeAuthority.RBI,
    )

    # 1. SIP exact query
    docs_sip = await retriever.retrieve("What is SIP?")
    assert len(docs_sip) > 0 and "SIP" in docs_sip[0].title

    # 2. SIP synonym query
    docs_sip_syn = await retriever.retrieve("What is systematic investment plan?")
    assert len(docs_sip_syn) > 0 and "SIP" in docs_sip_syn[0].title

    # 3. MF abbreviation
    docs_mf = await retriever.retrieve("MF kya hota hai?")
    assert len(docs_mf) > 0

    # 4. NAV query
    docs_nav = await retriever.retrieve("What is NAV?")
    assert len(docs_nav) > 0

    # 5. Riskometer -> SEBI
    docs_risk = await retriever.retrieve("What is riskometer?")
    assert len(docs_risk) > 0 and "SEBI" in str(docs_risk[0].metadata.get("authority")).upper()

    # 6. NPS -> PFRDA
    docs_nps = await retriever.retrieve("What is NPS?")
    assert len(docs_nps) > 0 and "PFRDA" in str(docs_nps[0].metadata.get("authority")).upper()

    # 7. TDS -> Income Tax
    docs_tds = await retriever.retrieve("What is TDS?")
    assert len(docs_tds) > 0 and "INCOME_TAX" in str(docs_tds[0].metadata.get("authority")).upper()

    # 8. KYC -> RBI
    docs_kyc = await retriever.retrieve("What is KYC?")
    assert len(docs_kyc) > 0 and "RBI" in str(docs_kyc[0].metadata.get("authority")).upper()

    # 9. Citation validity
    top_doc = docs_sip[0]
    assert top_doc.document_id and top_doc.title and top_doc.source

