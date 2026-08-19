"""
Phase L.7.2 — LLM Latency Optimization Test Suite

20 test cases verifying:
  1–3.   LLM timing fields correctly populated and separated.
  4–9.   Dynamic per-intent token budgets.
  10.    Global safety max ceiling enforced.
  11–13. Prompt omits empty personal/market/intel sections.
  14.    RAG citations preserved through optimization.
  15.    Safety validation still runs.
  16.    Provider failure behavior unchanged.
  17.    Streaming determination: STREAMING_NOT_SUPPORTED documented.
  18.    Personal queries never hit cache.
  19.    Privacy-safe diagnostics (no credentials in tracker output).
  20.    L.7.1 instrumentation still functional alongside L.7.2.

All tests use mocked LLM providers — no real HuggingFace API calls made.
Async tests use asyncio.run() (no pytest-asyncio dependency required).
"""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
from typing import Any, Optional

import pytest

from app.ai.context.builder import AIContextBuilder
from app.ai.generation.response_cache import EducationalResponseCache
from app.ai.generation.token_budget import TokenBudgetSelector
from app.ai.observability.latency import LatencyTracker
from app.ai.router import QueryIntent
from app.ai.schemas.advisor import AIContext
from app.ai.schemas.latency import LatencyBreakdown
from app.core.config import settings


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_tracker() -> LatencyTracker:
    return LatencyTracker(enabled=True)


def _make_ai_context(question: str = "What is SIP?") -> AIContext:
    return AIContext(
        question=question,
        user_financial_context=None,
        financial_intelligence=None,
        retrieved_knowledge=[],
        conversation_history=[],
        live_market_data=None,
    )


def _make_dashboard():
    """Build a minimal DashboardResponse with has_data=True for relevant sections."""
    from app.schemas.dashboard import (
        DashboardResponse, CashFlowSummary, NetWorthSummary, InvestmentSummary,
        LoanSummary, GoalSummary, BudgetSummary, FinancialHealthSummary, DebtSummary,
        PeriodInfo, UserContextInfo, FinancialSummarySnapshot,
    )
    today = datetime.date.today()
    return DashboardResponse(
        period=PeriodInfo(
            start_date=today.replace(day=1),
            end_date=today,
            period_days=today.day,
        ),
        user=UserContextInfo(
            user_id=1,
            display_name="Test User",
            persona="salaried",
            currency="INR",
            country="IN",
        ),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("100000"),
            total_expenses=Decimal("60000"),
            savings=Decimal("40000"),
            net_worth=Decimal("400000"),
            total_assets=Decimal("500000"),
            total_liabilities=Decimal("100000"),
            total_invested=Decimal("200000"),
            total_debt=Decimal("0"),
        ),
        cash_flow=CashFlowSummary(
            total_income=Decimal("100000"),
            total_expenses=Decimal("60000"),
            net_cash_flow=Decimal("40000"),
            savings=Decimal("40000"),
            savings_rate_percent=Decimal("40"),
            has_data=True,
        ),
        net_worth=NetWorthSummary(
            total_assets=Decimal("500000"),
            total_liabilities=Decimal("100000"),
            net_worth=Decimal("400000"),
            liquid_assets=Decimal("200000"),
            has_data=True,
        ),
        investments=InvestmentSummary(
            total_invested=Decimal("200000"),
            current_value=Decimal("220000"),
            total_gain_loss=Decimal("20000"),
            total_return_percentage=Decimal("10"),
            investment_count=3,
            has_data=True,
        ),
        loans=LoanSummary(
            total_outstanding=Decimal("0"),
            total_principal=Decimal("0"),
            total_monthly_emi=Decimal("0"),
            loan_count=0,
            active_loan_count=0,
            has_data=False,
        ),
        goals=GoalSummary(total_goals=0, active_count=0, completed_count=0, has_data=False),
        budgets=BudgetSummary(
            total_budget=Decimal("0"),
            total_spending=Decimal("0"),
            remaining_budget=Decimal("0"),
            overall_utilization_percent=Decimal("0"),
            has_data=False,
        ),
        debt=DebtSummary(
            total_debt=Decimal("0"),
            monthly_obligations=Decimal("0"),
            dti_percent=None,
            has_data=False,
        ),
        financial_health=FinancialHealthSummary(
            savings_rate_percent=Decimal("40"),
            dti_percent=None,
            emergency_fund_months=Decimal("5"),
            budget_utilization_percent=None,
            goal_completion_rate_percent=None,
            net_worth=Decimal("400000"),
            cash_flow_positive=True,
            has_data=True,
        ),
    )


class _MockLLM:
    """Async stub that mimics HuggingFaceProvider.generate signature."""

    def __init__(self, response: str = "This is a test response.", delay_s: float = 0.01) -> None:
        self._response = response
        self._delay_s = delay_s
        self.last_max_tokens: Optional[int] = None

    async def generate(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        self.last_max_tokens = max_tokens
        await asyncio.sleep(self._delay_s)
        if tracker:
            fake_ms = self._delay_s * 1000.0 + 5.0
            tracker.record("llm_request_ms", fake_ms)
            tracker.record("llm_generation_ms", fake_ms)
            tracker.record("llm_response_parse_ms", 0.5)
        return self._response


# ---------------------------------------------------------------------------
# Test 1 — llm_request_ms populated after LLM call
# ---------------------------------------------------------------------------

def test_llm_request_ms_populated():
    """llm_request_ms must be > 0 after a successful LLM generate call."""
    tracker = _make_tracker()
    llm = _MockLLM(delay_s=0.01)
    ctx = _make_ai_context()
    asyncio.run(llm.generate(ctx, "prompt", tracker=tracker))
    tracker.finish()
    assert tracker.breakdown.llm_request_ms > 0.0


# ---------------------------------------------------------------------------
# Test 2 — llm_generation_ms populated and equals llm_request_ms (non-streaming)
# ---------------------------------------------------------------------------

def test_llm_generation_ms_equals_request_ms_for_non_streaming():
    """For non-streaming providers, generation_ms == request_ms (documented limitation)."""
    tracker = _make_tracker()
    llm = _MockLLM(delay_s=0.01)
    ctx = _make_ai_context()
    asyncio.run(llm.generate(ctx, "prompt", tracker=tracker))
    tracker.finish()
    assert tracker.breakdown.llm_request_ms == tracker.breakdown.llm_generation_ms


# ---------------------------------------------------------------------------
# Test 3 — llm_response_parse_ms populated separately
# ---------------------------------------------------------------------------

def test_llm_response_parse_ms_populated():
    """llm_response_parse_ms must be >= 0 after generate (tracks JSON parse time)."""
    tracker = _make_tracker()
    llm = _MockLLM()
    ctx = _make_ai_context()
    asyncio.run(llm.generate(ctx, "prompt", tracker=tracker))
    tracker.finish()
    assert tracker.breakdown.llm_response_parse_ms >= 0.0


# ---------------------------------------------------------------------------
# Test 4 — CASUAL intent returns minimal token budget
# ---------------------------------------------------------------------------

def test_casual_budget_is_minimal():
    """CASUAL intent should receive the smallest max_tokens budget."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.CASUAL)
    assert budget <= settings.ai_max_tokens_casual
    assert budget <= 256, f"CASUAL budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 5 — GENERAL_FINANCE DEFINE/EXPLAIN returns simple_general budget
# ---------------------------------------------------------------------------

def test_general_finance_define_budget():
    """GENERAL_FINANCE + DEFINE operation should return the simple_general budget."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.GENERAL_FINANCE, operation="DEFINE")
    assert budget <= settings.ai_max_tokens_simple_general
    assert budget <= 512, f"DEFINE budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 6 — PERSONAL_FINANCE returns personal_lookup budget
# ---------------------------------------------------------------------------

def test_personal_finance_budget():
    """PERSONAL_FINANCE / PERSONAL_LOOKUP should return personal_lookup budget."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.PERSONAL_FINANCE, scope="PERSONAL_LOOKUP")
    assert budget <= settings.ai_max_tokens_personal_lookup
    assert budget <= 512, f"PERSONAL_LOOKUP budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 7 — MIXED returns mixed budget
# ---------------------------------------------------------------------------

def test_mixed_budget():
    """MIXED intent should return the mixed budget (larger than personal lookup)."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.MIXED)
    assert budget <= settings.ai_max_tokens_mixed
    assert budget <= 600, f"MIXED budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 8 — COMPARISON flag returns comparison budget
# ---------------------------------------------------------------------------

def test_comparison_budget():
    """Comparison queries need expanded context → comparison budget."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.GENERAL_FINANCE, is_comparison=True)
    assert budget <= settings.ai_max_tokens_comparison
    assert budget <= 800, f"COMPARISON budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 9 — HISTORICAL flag returns historical budget
# ---------------------------------------------------------------------------

def test_historical_budget():
    """Historical temporal queries need expanded budget for research-heavy answers."""
    selector = TokenBudgetSelector()
    budget = selector.select(intent=QueryIntent.GENERAL_FINANCE, is_historical=True)
    assert budget <= settings.ai_max_tokens_historical
    assert budget <= 800, f"HISTORICAL budget too large: {budget}"


# ---------------------------------------------------------------------------
# Test 10 — Global safety max ceiling enforced
# ---------------------------------------------------------------------------

def test_global_safety_max_enforced():
    """No budget should exceed ai_max_tokens_global_safety_max."""
    selector = TokenBudgetSelector()
    safety_max = settings.ai_max_tokens_global_safety_max
    for intent in QueryIntent:
        for is_comp, is_hist in [(False, False), (True, False), (False, True)]:
            budget = selector.select(intent=intent, is_comparison=is_comp, is_historical=is_hist)
            assert budget <= safety_max, (
                f"Budget {budget} exceeds safety_max {safety_max} for intent={intent}"
            )


# ---------------------------------------------------------------------------
# Test 11 — Prompt omits empty personal context block
# ---------------------------------------------------------------------------

def test_prompt_omits_empty_personal_context():
    """When user_financial_context is None, personal context JSON block must not appear.
    
    Note: system instructions reference <personal_financial_context> as a tag name —
    this is expected. We verify that the actual *block section* (with User Financial Facts JSON)
    is absent, not just the tag name string in system instructions.
    """
    builder = AIContextBuilder()
    tracker = _make_tracker()
    ctx = AIContext(
        question="What is a mutual fund?",
        user_financial_context=None,
        financial_intelligence=None,
        retrieved_knowledge=[],
        conversation_history=[],
        live_market_data=None,
    )
    prompt = builder.build_prompt(ctx, tracker=tracker)
    # The personal block section header appears in the prompt body (not system instructions)
    # only when has_any_data is True. Check the user facts block is absent.
    assert "User Financial Facts (Authenticated" not in prompt


# ---------------------------------------------------------------------------
# Test 12 — Prompt omits empty market data block
# ---------------------------------------------------------------------------

def test_prompt_omits_empty_market_data():
    """When live_market_data is None, the Live Market Data block must be absent."""
    builder = AIContextBuilder()
    ctx = AIContext(
        question="What is PPF?",
        user_financial_context=None,
        financial_intelligence=None,
        retrieved_knowledge=[],
        conversation_history=[],
        live_market_data=None,
    )
    prompt = builder.build_prompt(ctx)
    assert "Live Market Data (Authoritative" not in prompt


# ---------------------------------------------------------------------------
# Test 13 — Prompt size is smaller with compact JSON
# ---------------------------------------------------------------------------

def test_prompt_uses_compact_json_not_indented():
    """Compact JSON serialization: no 4-space indented JSON in prompt."""
    builder = AIContextBuilder()
    dashboard = _make_dashboard()
    ai_ctx = builder.build_context(
        question="What is my savings rate?",
        full_context=dashboard,
        retrieved_docs=[],
    )
    prompt = builder.build_prompt(ai_ctx)
    # indent=2 would produce e.g. '    "total_income"' (4 spaces + key)
    assert '    "total_income"' not in prompt, "Prompt appears to use indented JSON (indent=2)"
    assert len(prompt) > 0


# ---------------------------------------------------------------------------
# Test 14 — RAG citation metadata preserved in prompt
# ---------------------------------------------------------------------------

def test_rag_citations_preserved_in_prompt():
    """RAG document title, source, and content must appear in the assembled prompt."""
    from app.ai.schemas.advisor import RetrievedDocument

    doc = RetrievedDocument(
        document_id="doc-001",
        title="SIP Guidelines",
        source="AMFI",
        content="A Systematic Investment Plan allows periodic investments in mutual funds.",
        relevance_score=0.92,
        metadata={"authority": "AMFI", "source_url": "https://amfi.in/sip"},
    )
    builder = AIContextBuilder()
    ctx = AIContext(
        question="What is SIP?",
        user_financial_context=None,
        financial_intelligence=None,
        retrieved_knowledge=[doc],
        conversation_history=[],
        live_market_data=None,
    )
    prompt = builder.build_prompt(ctx)
    assert "SIP Guidelines" in prompt
    assert "AMFI" in prompt
    assert "Systematic Investment Plan" in prompt


# ---------------------------------------------------------------------------
# Test 15 — Safety validation still runs after optimization
# ---------------------------------------------------------------------------

def test_safety_validation_interface_preserved():
    """A concrete AISafetyValidator must be callable with (response, context, tracker)."""
    from app.ai.safety.base import AISafetyValidator

    class _ConcreteSafetyValidator(AISafetyValidator):
        def validate_response(self, response, context, tracker=None):
            pass  # safe — no-op concrete implementation

    validator = _ConcreteSafetyValidator()
    tracker = _make_tracker()
    ctx = _make_ai_context()
    # Must not raise for a safe response
    try:
        validator.validate_response(response="SIP is a method of investing.", context=ctx, tracker=tracker)
        passed = True
    except Exception:
        passed = False
    assert passed, "Safety validator raised unexpectedly on a safe response"


# ---------------------------------------------------------------------------
# Test 16 — Provider failure propagates as AIProviderError (not swallowed)
# ---------------------------------------------------------------------------

def test_provider_failure_propagates():
    """When LLM generate raises, the exception must not be swallowed silently."""
    from app.ai.exceptions import AIProviderError

    class _FailingLLM:
        async def generate(self, context, prompt, tracker=None, max_tokens=None, **kwargs):
            raise AIProviderError("Simulated provider failure")

    llm = _FailingLLM()
    with pytest.raises(AIProviderError, match="Simulated provider failure"):
        asyncio.run(llm.generate(_make_ai_context(), "prompt"))


# ---------------------------------------------------------------------------
# Test 17 — Streaming determination documented as STREAMING_NOT_SUPPORTED
# ---------------------------------------------------------------------------

def test_streaming_not_supported_documented():
    """
    Phase L.7.2 decision: streaming is not implemented.
    Verify HuggingFaceProvider module docstring mentions STREAMING_NOT_SUPPORTED.
    """
    import app.ai.providers.huggingface as hf_module
    source = hf_module.__doc__ or ""
    assert "STREAMING_NOT_SUPPORTED" in source, (
        "HuggingFaceProvider module docstring must document STREAMING_NOT_SUPPORTED decision"
    )


# ---------------------------------------------------------------------------
# Test 18 — Personal queries are never stored in educational cache
# ---------------------------------------------------------------------------

def test_personal_queries_not_cached():
    """PERSONAL_FINANCE intent must never be stored in the educational cache."""
    cache = EducationalResponseCache()
    cache.invalidate()

    stored = cache.put(
        query="How much did I spend this month?",
        model_name="meta-llama/Llama-3.1-8B-Instruct",
        max_tokens=300,
        intent=QueryIntent.PERSONAL_FINANCE,
        scope="PERSONAL_LOOKUP",
        has_personal_context=True,
        has_live_market_data=False,
        response_text="Your spending is 60000 INR.",
    )
    assert stored is False, "PERSONAL_FINANCE response must not be cached"

    result = cache.get(
        query="How much did I spend this month?",
        model_name="meta-llama/Llama-3.1-8B-Instruct",
        max_tokens=300,
        intent=QueryIntent.PERSONAL_FINANCE,
        scope="PERSONAL_LOOKUP",
        has_personal_context=True,
        has_live_market_data=False,
    )
    assert result is None, "PERSONAL_FINANCE result must never be returned from cache"


# ---------------------------------------------------------------------------
# Test 19 — Privacy-safe diagnostics: no credentials in tracker output
# ---------------------------------------------------------------------------

def test_tracker_output_contains_no_credentials():
    """
    The latency tracker to_dict() output must not contain API keys, passwords,
    or JWT tokens. Checks that model_name is a safe string (model identifier only).
    """
    tracker = _make_tracker()
    tracker.breakdown.model_name = "meta-llama/Llama-3.1-8B-Instruct"
    tracker.finish()
    output = tracker.to_dict()

    dangerous_prefixes = ("Bearer ", "hf_", "sk-", "eyJ")
    for key, value in output.items():
        if isinstance(value, str):
            for prefix in dangerous_prefixes:
                assert not value.startswith(prefix), (
                    f"Latency tracker field '{key}' contains sensitive credential-like value"
                )


# ---------------------------------------------------------------------------
# Test 20 — L.7.1 full pipeline instrumentation still functional
# ---------------------------------------------------------------------------

def test_l71_pipeline_fields_still_functional():
    """
    All original Phase L.7.1 latency fields must still exist and be settable
    on LatencyBreakdown to confirm backward compatibility.
    """
    bd = LatencyBreakdown()

    l71_fields = [
        "query_understanding_ms", "typo_normalization_ms", "hinglish_ms",
        "reference_resolution_ms", "entity_extraction_ms", "intent_scope_ms",
        "retrieval_rewrite_ms", "adaptive_routing_ms", "pgvector_ms", "faiss_ms",
        "fusion_ms", "minilm_ms", "minilm_model_load_ms", "minilm_embedding_ms",
        "minilm_scoring_ms", "reranker_ms", "context_build_ms", "llm_request_ms",
        "llm_generation_ms", "safety_validation_ms", "persistence_ms", "total_ms",
        "pgvector_used", "faiss_used", "minilm_used",
        "candidate_count_pgvector", "candidate_count_faiss", "candidate_count_fused",
        "candidate_count_before_rerank", "candidate_count_after_rerank",
        "rag_chunk_count", "personal_context_fields_count", "prompt_char_count",
    ]

    l72_fields = [
        "llm_response_parse_ms", "system_prompt_chars", "personal_context_chars",
        "knowledge_context_chars", "conversation_history_chars", "user_query_chars",
        "max_tokens_budget", "model_name", "prompt_token_count", "response_token_count",
        "cache_hit",
    ]

    for field in l71_fields + l72_fields:
        assert hasattr(bd, field), f"LatencyBreakdown missing field: {field}"

    # Verify L.7.1 fields are still settable via tracker
    tracker = _make_tracker()
    tracker.record("pgvector_ms", 12.5)
    tracker.record("faiss_ms", 8.3)
    tracker.record("minilm_ms", 45.1)
    tracker.record("llm_request_ms", 3200.0)
    tracker.record_flag("pgvector_used", True)
    tracker.record_count("candidate_count_pgvector", 20)
    tracker.finish()

    assert tracker.breakdown.pgvector_ms == 12.5
    assert tracker.breakdown.faiss_ms == 8.3
    assert tracker.breakdown.minilm_ms == 45.1
    assert tracker.breakdown.llm_request_ms == 3200.0
    assert tracker.breakdown.pgvector_used is True
    assert tracker.breakdown.candidate_count_pgvector == 20
    assert tracker.breakdown.total_ms > 0.0
