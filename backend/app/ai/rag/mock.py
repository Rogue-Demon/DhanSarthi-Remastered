"""
Mock RAG retriever and vector store implementations for unit testing.
"""

from __future__ import annotations

from app.ai.rag.base import RAGRetriever, VectorStore
from app.ai.schemas.advisor import RetrievedDocument


class MockRAGRetriever(RAGRetriever):
    """Returns static, canned financial knowledge documents matching the query keywords."""

    def __init__(self) -> None:
        self.last_query = ""
        self.last_filters = None
        self.db = [
            RetrievedDocument(
                document_id="doc_1",
                title="Systematic Investment Plan (SIP) Guidelines",
                content="A Systematic Investment Plan (SIP) allows investors to invest a fixed amount regularly (monthly or quarterly) in mutual funds. It promotes regular savings and benefits from rupee cost averaging, reducing the impact of market volatility.",
                source="Association of Mutual Funds",
                relevance_score=0.95,
                metadata={"category": "INVESTMENT", "country": "IN", "version": "1.0"},
            ),
            RetrievedDocument(
                document_id="doc_2",
                title="Personal Loan Affordability Standards",
                content="Lenders evaluate loan applications using the Debt-to-Income (DTI) ratio. A DTI under 36% is considered healthy, while a DTI above 45% represents a high debt burden. The monthly EMI obligation includes both principal and interest components calculated using a reducing-balance formula.",
                source="Reserve Bank Regulations",
                relevance_score=0.88,
                metadata={"category": "LOANS", "country": "IN", "version": "2.4"},
            ),
            RetrievedDocument(
                document_id="doc_3",
                title="Tax Deductions under Section 80C",
                content="Under Section 80C of the Income Tax Act, individuals can claim deductions up to ₹1.5 lakh per financial year for investments in eligible instruments like ELSS, PPF, NPS, and life insurance premiums.",
                source="Income Tax Department",
                relevance_score=0.92,
                metadata={"category": "TAX", "country": "IN", "financial_year": "2026-27"},
            ),
        ]

    async def retrieve(
        self, query: str, filters: dict | None = None
    ) -> list[RetrievedDocument]:
        self.last_query = query
        self.last_filters = filters

        q = query.lower()
        results = []

        # Simple keyword matching to simulate vector similarity
        if any(kw in q for kw in ["sip", "invest", "mutual fund"]):
            results.append(self.db[0])
        if any(kw in q for kw in ["loan", "emi", "dti", "debt"]):
            results.append(self.db[1])
        if any(kw in q for kw in ["tax", "80c", "deduction"]):
            results.append(self.db[2])

        # If no keywords matched, return everything as generic knowledge
        if not results:
            results = self.db

        return results


class MockVectorStore(VectorStore):
    """Mock database vector store for testing similarity searches."""

    async def similarity_search(
        self, embedding: list[float], limit: int = 5
    ) -> list[RetrievedDocument]:
        # Return mock matching documents
        retriever = MockRAGRetriever()
        return retriever.db[:limit]
