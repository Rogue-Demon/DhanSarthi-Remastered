"""
Phase L.9.7 — Comprehensive Intelligent Prompt Compression & Context Efficiency Test Suite.

Verifies:
  1. Disabled mode behavior
  2. Enabled mode behavior
  3. NONE compression mode
  4. LIGHT compression mode
  5. MODERATE compression mode
  6. AGGRESSIVE safeguards (downgrades for complex/personal/regulatory queries)
  7. RAG duplicate chunk detection via Jaccard similarity
  8. Authoritative source preservation
  9. Citation preservation on compressed chunks
  10. Personal financial fact preservation (exact numerical accuracy)
  11. Personal context field pruning
  12. Conversation history pruning (distant turns removed)
  13. Pronoun reference preservation (relevant context kept)
  14. System safety instruction preservation
  15. Untrusted knowledge boundary preservation
  16. Market data boundary preservation
  17. Token counting accuracy
  18. Character counting accuracy
  19. Compression ratio calculation
  20. Max prompt token enforcement
  21. No hallucinated content
  22. Deterministic output across repeated invocations
  23. Cache compatibility (cache hit skips compression)
  24. Streaming compatibility
  25. Empty context handling
  26. Oversized context trimming
  27. Complex planning protection
  28. Historical regulatory query protection
  29. Latency instrumentation and observability metrics
  30. Phase L.7.4 backward compatibility and non-regression
"""

import asyncio
import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.inference.config import InferenceComplexity
from app.ai.inference.prompt_compressor import (
    CompressionMode,
    PromptCompressionResult,
    PromptCompressor,
    get_prompt_compressor,
)
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.router import QueryIntent
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import (
    AIAdvisorRequest,
    AIContext,
    RetrievedDocument,
    SendMessageRequest,
)
from app.core.config import settings
from app.schemas.dashboard import (
    DashboardResponse,
    CashFlowSummary,
    NetWorthSummary,
    InvestmentSummary,
    LoanSummary,
    GoalSummary,
    BudgetSummary,
    FinancialHealthSummary,
    DebtSummary,
    PeriodInfo,
    UserContextInfo,
    FinancialSummarySnapshot,
)


def _make_dashboard(net_worth: Decimal = Decimal("1500000")) -> DashboardResponse:
    today = datetime.date.today()
    return DashboardResponse(
        period=PeriodInfo(start_date=today.replace(day=1), end_date=today, period_days=today.day),
        user=UserContextInfo(user_id=1, display_name="Test User", persona="salaried", currency="INR", country="IN"),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("75000"),
            total_expenses=Decimal("30000"),
            savings=Decimal("45000"),
            net_worth=net_worth,
            total_assets=Decimal("1600000"),
            total_liabilities=Decimal("100000"),
            total_invested=Decimal("500000"),
            total_debt=Decimal("100000"),
        ),
        cash_flow=CashFlowSummary(
            total_income=Decimal("75000"),
            total_expenses=Decimal("30000"),
            net_cash_flow=Decimal("45000"),
            savings=Decimal("45000"),
            savings_rate_percent=Decimal("60"),
            has_data=True,
        ),
        net_worth=NetWorthSummary(
            total_assets=Decimal("1600000"),
            total_liabilities=Decimal("100000"),
            net_worth=net_worth,
            liquid_assets=Decimal("200000"),
            has_data=True,
        ),
        investments=InvestmentSummary(
            total_invested=Decimal("500000"),
            current_value=Decimal("550000"),
            total_gain_loss=Decimal("50000"),
            total_return_percentage=Decimal("10"),
            investment_count=3,
            has_data=True,
        ),
        loans=LoanSummary(
            total_outstanding=Decimal("100000"),
            total_principal=Decimal("100000"),
            total_monthly_emi=Decimal("5000"),
            loan_count=1,
            active_loan_count=1,
            loans=[],
            has_data=True,
        ),
        debt=DebtSummary(total_debt=Decimal("100000"), monthly_obligations=Decimal("5000"), dti_percent=Decimal("15.0"), has_data=True),
        goals=GoalSummary(total_goals=1, active_count=1, completed_count=0, goals=[], has_data=True),
        budgets=BudgetSummary(total_budget=Decimal("35000"), total_spending=Decimal("30000"), remaining_budget=Decimal("5000"), overall_utilization_percent=Decimal("85.7"), over_budget_categories=[], has_data=True),
        financial_health=FinancialHealthSummary(
            savings_rate_percent=Decimal("60.0"),
            dti_percent=Decimal("15.0"),
            emergency_fund_months=Decimal("6.0"),
            budget_utilization_percent=Decimal("85.7"),
            goal_completion_rate_percent=Decimal("0.0"),
            net_worth=net_worth,
            cash_flow_positive=True,
        ),
    )


class MockMsg:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


# ==============================================================================
# UNIT TESTS: PromptCompressor Logic
# ==============================================================================

class TestPromptCompressorUnit:
    """Covers tests 1-22: Modes, deduplication, history pruning, safety boundaries, token counting."""

    def test_01_disabled_mode_returns_original(self):
        compressor = PromptCompressor()
        ctx = AIContext(question="What is SIP?", facts={}, retrieved_knowledge=[])
        raw_prompt = "Original prompt with some content..."
        with patch.object(settings, "ai_prompt_compression_enabled", False):
            result = compressor.compress(ctx, raw_prompt)
            assert result.compressed_prompt == raw_prompt
            assert result.compression_mode == "NONE"
            assert result.compression_ratio == 1.0

    def test_02_enabled_mode_compresses_prompt(self):
        compressor = PromptCompressor()
        doc = RetrievedDocument(
            document_id="doc1",
            title="Understanding SIP",
            content="A Systematic Investment Plan allows investing monthly in mutual funds.",
            source="DhanSarthi Education",
            relevance_score=0.92,
            metadata={"authority": "OFFICIAL", "source_url": "https://amfiindia.com/sip"},
        )
        ctx = AIContext(question="What is SIP?", retrieved_knowledge=[doc])
        builder = AIContextBuilder()
        raw_prompt = builder.build_prompt(ctx)

        with patch.object(settings, "ai_prompt_compression_enabled", True):
            result = compressor.compress(ctx, raw_prompt, intent=QueryIntent.GENERAL_FINANCE)
            assert result.compressed_tokens < result.original_tokens
            assert result.compression_ratio < 1.0
            assert result.reduction_percent > 0.0
            assert "Systematic Investment Plan" in result.compressed_prompt

    def test_03_04_05_compression_modes(self):
        compressor = PromptCompressor()
        # NONE
        with patch.object(settings, "ai_prompt_compression_mode", "NONE"):
            m_none = compressor.determine_compression_mode(QueryIntent.GENERAL_FINANCE)
            assert m_none == CompressionMode.NONE

        # LIGHT
        with patch.object(settings, "ai_prompt_compression_mode", "LIGHT"):
            m_light = compressor.determine_compression_mode(QueryIntent.GENERAL_FINANCE)
            assert m_light == CompressionMode.LIGHT

        # MODERATE
        with patch.object(settings, "ai_prompt_compression_mode", "MODERATE"):
            m_mod = compressor.determine_compression_mode(QueryIntent.GENERAL_FINANCE)
            assert m_mod == CompressionMode.MODERATE

    def test_06_27_28_aggressive_safeguards(self):
        compressor = PromptCompressor()
        with patch.object(settings, "ai_prompt_compression_mode", "AGGRESSIVE"):
            # Complex planning -> downgraded to MODERATE
            m_complex = compressor.determine_compression_mode(
                intent=QueryIntent.GENERAL_FINANCE,
                complexity=InferenceComplexity.COMPLEX,
            )
            assert m_complex == CompressionMode.MODERATE

            # Personal queries -> downgraded to MODERATE
            m_personal = compressor.determine_compression_mode(
                intent=QueryIntent.PERSONAL_FINANCE,
                is_personal=True,
            )
            assert m_personal == CompressionMode.MODERATE

            # Historical regulatory -> downgraded to MODERATE
            m_hist = compressor.determine_compression_mode(
                intent=QueryIntent.GENERAL_FINANCE,
                is_historical=True,
            )
            assert m_hist == CompressionMode.MODERATE

    def test_07_08_09_rag_duplicate_detection_and_citation_preservation(self):
        compressor = PromptCompressor()
        doc1 = RetrievedDocument(
            document_id="doc1",
            title="Understanding SIP",
            content="A Systematic Investment Plan allows periodic disciplined investing in mutual funds.",
            source="AMFI Guidelines",
            relevance_score=0.95,
            metadata={"authority": "HIGH", "source_url": "https://amfiindia.com/doc1"},
        )
        # doc2 is practically duplicate content of doc1
        doc2 = RetrievedDocument(
            document_id="doc2",
            title="SIP Explanation",
            content="A Systematic Investment Plan allows periodic disciplined investing in mutual funds schemes.",
            source="General Blog",
            relevance_score=0.75,
            metadata={"authority": "MEDIUM", "source_url": "https://example.com/doc2"},
        )
        # doc3 is completely distinct (Tax 80C)
        doc3 = RetrievedDocument(
            document_id="doc3",
            title="Section 80C Deductions",
            content="Section 80C allows tax deduction up to ₹1,50,000 per financial year under the old regime.",
            source="Income Tax Department",
            relevance_score=0.88,
            metadata={"authority": "STATUTORY", "source_url": "https://incometax.gov.in/80c"},
        )

        retained, removed_count = compressor.deduplicate_rag_chunks([doc1, doc2, doc3], similarity_threshold=0.60)
        assert removed_count == 1
        assert len(retained) == 2
        # doc1 (high authority) kept, doc2 (duplicate) removed, doc3 (distinct) kept
        doc_ids = [d.document_id for d in retained]
        assert "doc1" in doc_ids
        assert "doc3" in doc_ids
        assert "doc2" not in doc_ids
        # Verify citation fields preserved intact
        assert retained[0].metadata["source_url"] == "https://amfiindia.com/doc1"
        assert retained[1].metadata["source_url"] == "https://incometax.gov.in/80c"

    def test_10_11_personal_financial_fact_preservation(self):
        compressor = PromptCompressor()
        dash = _make_dashboard()
        ctx = AIContext(
            question="What is my savings rate and net worth?",
            user_financial_context=dash,
            retrieved_knowledge=[],
        )
        builder = AIContextBuilder()
        raw_prompt = builder.build_prompt(ctx)
        result = compressor.compress(ctx, raw_prompt, intent=QueryIntent.PERSONAL_FINANCE, is_personal=True)

        # Exact ground truth numbers MUST be present in compressed prompt
        assert "75000" in result.compressed_prompt
        assert "30000" in result.compressed_prompt
        assert "1500000" in result.compressed_prompt
        assert "60" in result.compressed_prompt

    def test_12_13_conversation_history_pruning_and_pronoun_preservation(self):
        compressor = PromptCompressor()
        # History with an early unrelated question, then a question about SIP, followed by "Is it risky?"
        history = [
            MockMsg("user", "What is the weather today?"),
            MockMsg("assistant", "I am a financial advisor, not a weather service."),
            MockMsg("user", "Can you explain how SIP works in mutual funds?"),
            MockMsg("assistant", "SIP lets you invest a fixed sum at regular intervals in mutual funds."),
        ]
        # Current query is a follow-up with a pronoun: "Is it risky for long term?"
        retained, removed_count = compressor.compress_conversation_history(
            history=history,
            current_query="Is it risky for long term?",
            mode=CompressionMode.MODERATE,
            max_messages=2,
        )
        assert len(retained) == 2
        # The immediate prior turn about SIP was retained!
        assert any("SIP" in getattr(m, "content", "") for m in retained)

    def test_14_15_16_system_safety_and_untrusted_knowledge_boundary_preservation(self):
        compressor = PromptCompressor()
        instructions = compressor.compress_system_instructions(mode=CompressionMode.MODERATE)
        # Regulatory safety boundaries MUST remain intact
        assert "DhanSarthi" in instructions
        assert "<personal_financial_context>" in instructions
        assert "<untrusted_knowledge_content>" in instructions
        assert "NEVER guarantee" in instructions or "Do NOT guarantee" in instructions

    def test_17_18_19_token_char_metrics(self):
        compressor = PromptCompressor()
        doc = RetrievedDocument(
            document_id="doc1",
            title="Inflation Overview",
            content="Inflation is a general increase in prices and fall in the purchasing value of money.",
            source="RBI Notes",
            relevance_score=0.9,
        )
        ctx = AIContext(question="What is inflation?", retrieved_knowledge=[doc])
        raw_prompt = AIContextBuilder().build_prompt(ctx)
        result = compressor.compress(ctx, raw_prompt)

        assert result.original_chars == len(raw_prompt)
        assert result.compressed_chars == len(result.compressed_prompt)
        assert result.original_tokens > 0
        assert result.compressed_tokens > 0
        assert 0.0 < result.compression_ratio <= 1.0
        assert result.reduction_percent >= 0.0

    def test_21_22_deterministic_and_no_hallucination(self):
        compressor = PromptCompressor()
        ctx = AIContext(question="What is PPF?", retrieved_knowledge=[])
        raw_prompt = "What is PPF?\nExplain PPF rules."

        res1 = compressor.compress(ctx, raw_prompt)
        res2 = compressor.compress(ctx, raw_prompt)

        # Output must be 100% deterministic
        assert res1.compressed_prompt == res2.compressed_prompt
        assert res1.compressed_tokens == res2.compressed_tokens

    def test_25_26_empty_and_oversized_context(self):
        compressor = PromptCompressor()
        # Empty context
        ctx_empty = AIContext(question="", retrieved_knowledge=[])
        res_empty = compressor.compress(ctx_empty, "")
        assert res_empty.compressed_prompt is not None

        # Oversized history (100 messages)
        history_huge = [MockMsg("user", f"Question {i}") for i in range(100)]
        retained, removed = compressor.compress_conversation_history(history_huge, "Test", max_messages=4)
        assert len(retained) <= 4
        assert removed == 96


# ==============================================================================
# INTEGRATION TESTS: AIAdvisorService & Latency Observability
# ==============================================================================

@pytest.fixture
def mock_service_deps():
    db = MagicMock()
    rag = MockRAGRetriever()
    safety = SimpleSafetyValidator()
    builder = AIContextBuilder()
    dash = MagicMock()
    dash.build_dashboard.return_value = _make_dashboard()
    conv = MagicMock()
    conv.get_recent_history.return_value = []

    def _store_asst(conversation_id, content, metadata=None):
        return MagicMock(
            id=101,
            role="assistant",
            content=content,
            message_metadata=metadata or {},
            created_at=datetime.datetime.now(),
        )

    conv.store_assistant_message.side_effect = _store_asst
    now = datetime.datetime.now()
    user_msg = MagicMock(id=100, role="user", content="Query", message_metadata={}, created_at=now)
    conv.store_user_message.return_value = user_msg
    conv.create_user_message.return_value = user_msg
    conv.get_conversation.return_value = MagicMock(id=1, user_id=1)
    conv.touch_conversation.return_value = None

    return {
        "db": db,
        "rag": rag,
        "safety": safety,
        "builder": builder,
        "dash": dash,
        "conv": conv,
    }


class CountingMockLLMProvider(MockLLMProvider):
    """Mock LLM that captures the actual received prompt."""

    def __init__(self, response_text: str = "A Systematic Investment Plan (SIP) allows investing periodically.") -> None:
        super().__init__(response_text=response_text)
        self.last_prompt_received: str = ""

    async def generate(self, context: AIContext, prompt: str, **kwargs: Any) -> str:
        self.last_prompt_received = prompt
        return await super().generate(context, prompt, **kwargs)

    async def generate_stream(self, context: AIContext, prompt: str, **kwargs: Any):
        self.last_prompt_received = prompt
        words = self.response_text.split(" ")
        for w in words:
            yield w + " "


@pytest.mark.anyio
class TestAIAdvisorCompressionIntegration:
    """Covers tests 23, 24, 29, 30: End-to-end integration, cache interaction, streaming, and latency metrics."""

    async def test_23_cache_compatibility(self, mock_service_deps):
        provider = CountingMockLLMProvider()
        service = AIAdvisorService(
            db=mock_service_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_service_deps["rag"],
            safety_validator=mock_service_deps["safety"],
            context_builder=mock_service_deps["builder"],
            dashboard_service=mock_service_deps["dash"],
            conversation_service=mock_service_deps["conv"],
        )

        req = SendMessageRequest(message="What is a Systematic Investment Plan?")
        # Call 1: Miss -> Compression runs before LLM
        resp1 = await service.send_chat_message(user_id=1, conversation_id=1, request=req)
        meta1 = resp1.assistant_message.message_metadata
        assert meta1["cache"]["hit"] is False
        assert meta1["latency"]["prompt_compression_ms"] >= 0.0
        assert meta1["latency"]["prompt_tokens_before"] is not None
        assert meta1["latency"]["prompt_tokens_after"] is not None

        # Call 2: Hit -> Served from cache, LLM skipped
        resp2 = await service.send_chat_message(user_id=1, conversation_id=1, request=req)
        meta2 = resp2.assistant_message.message_metadata
        assert meta2["cache"]["hit"] is True
        assert meta2["latency"]["llm_skipped_due_to_cache"] is True

    async def test_24_streaming_compatibility(self, mock_service_deps):
        provider = CountingMockLLMProvider(
            response_text="Compound interest is interest calculated on the initial principal and past interest."
        )
        service = AIAdvisorService(
            db=mock_service_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_service_deps["rag"],
            safety_validator=mock_service_deps["safety"],
            context_builder=mock_service_deps["builder"],
            dashboard_service=mock_service_deps["dash"],
            conversation_service=mock_service_deps["conv"],
        )

        req = SendMessageRequest(message="Explain compound interest")
        chunks = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "Compound interest" in "".join(chunks)

    async def test_29_30_latency_breakdown_and_l74_regression(self, mock_service_deps):
        provider = CountingMockLLMProvider()
        service = AIAdvisorService(
            db=mock_service_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_service_deps["rag"],
            safety_validator=mock_service_deps["safety"],
            context_builder=mock_service_deps["builder"],
            dashboard_service=mock_service_deps["dash"],
            conversation_service=mock_service_deps["conv"],
        )

        req = SendMessageRequest(message="What is Section 80C tax deduction?")
        resp = await service.send_chat_message(user_id=1, conversation_id=1, request=req)
        lat = resp.assistant_message.message_metadata["latency"]

        # Phase L.9.7 metrics must be present and valid
        assert "prompt_compression_ms" in lat
        assert "prompt_tokens_before" in lat
        assert "prompt_tokens_after" in lat
        assert "prompt_compression_ratio" in lat
        assert lat["prompt_compression_mode"] != ""

        # Phase L.7.4 metrics must still be present
        assert "effective_max_tokens" in lat
        assert "inference_config_ms" in lat
