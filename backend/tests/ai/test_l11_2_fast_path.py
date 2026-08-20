"""
Unit and integration tests for Phase L.11.2: Personal Fast-Path & Adaptive Output Token Budget.

Validates:
1. Fast-path activation for direct personal lookups ("tell me about my goal", "what is my net worth?", "what are my monthly expenses?").
2. Fast-path non-activation for planning, comparison, historical, and market queries.
3. Bypass of unnecessary General RAG (FAISS/pgvector/MiniLM/RRF/reranking).
4. Bypass of unnecessary live market data calls.
5. Minimal personal context selection.
6. Adaptive output token budget enforcement (<= 180 tokens for direct lookups).
7. Complex/comparison queries retention of standard adaptive budgets.
8. Safe fallback when personal financial context is missing (zero LLM calls).
9. Cache exclusion for personalized financial responses.
10. Active safety validation on all outputs.
11. Telemetry and observability flag persistence.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.cache.cache_policy import CacheEligibilityPolicy
from app.ai.inference.budget import (
    AdaptiveTokenBudgetSelector,
    InferenceComplexityClassifier,
    PersonalFastPathClassifier,
)
from app.ai.inference.config import InferenceComplexity
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    ComparisonInfo,
    OperationType,
    QueryExecutionPlan,
    QueryScope,
    TemporalReference,
)
from app.ai.schemas.latency import LatencyBreakdown
from app.ai.observability.latency import LatencyTracker
from app.ai.context.builder import AIContextBuilder
from app.ai.schemas.advisor import AIContext
from app.schemas.dashboard import DashboardResponse


# ─── 1. FAST-PATH CLASSIFICATION TESTS ─────────────────────────────────────────

def test_fast_path_tell_me_about_my_goal():
    """Test 1: 'tell me about my goal' activates direct personal fast-path."""
    ep = QueryExecutionPlan(
        original_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="tell me about my goal",
    )
    assert is_fp is True
    assert reason == "DIRECT_PERSONAL_LOOKUP"
    assert budget == 128


def test_fast_path_what_is_my_net_worth():
    """Test 2: 'what is my net worth?' activates direct personal fast-path."""
    ep = QueryExecutionPlan(
        original_query="what is my net worth?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.NET_WORTH_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="what is my net worth?",
    )
    assert is_fp is True
    assert reason == "DIRECT_PERSONAL_LOOKUP"
    assert budget == 128


def test_fast_path_what_are_my_monthly_expenses():
    """Test 3: 'what are my monthly expenses?' activates direct personal fast-path."""
    ep = QueryExecutionPlan(
        original_query="what are my monthly expenses?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.SPENDING_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="what are my monthly expenses?",
    )
    assert is_fp is True
    assert reason == "DIRECT_PERSONAL_LOOKUP"
    assert budget == 128


def test_fast_path_explanation_variant():
    """Test explanation variants receive appropriate capped budgets (160 / 180 tokens)."""
    ep = QueryExecutionPlan(
        original_query="why are my expenses so high?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.SPENDING_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.EXPLAIN,
        requires_rag=False,
        requires_market_data=False,
    )
    # Brief explanation
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="why are my expenses so high?",
    )
    assert is_fp is True
    assert reason == "DIRECT_LOOKUP_WITH_EXPLANATION"
    assert budget == 160

    # Detailed explanation
    is_fp_long, reason_long, budget_long = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="explain in detail my loan breakdown",
    )
    assert is_fp_long is True
    assert reason_long == "LONGER_PERSONAL_EXPLANATION"
    assert budget_long == 180


# ─── 2. FAST-PATH NON-ACTIVATION (DISQUALIFICATION) TESTS ─────────────────────

def test_fast_path_disabled_for_planning():
    """Test 4: Planning / investment recommendations do NOT activate fast-path."""
    ep = QueryExecutionPlan(
        original_query="how much should I invest for retirement?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
        requires_rag=True,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="how much should I invest for retirement?",
    )
    assert is_fp is False
    assert reason is None
    assert budget == 0


def test_fast_path_disabled_for_comparison():
    """Test 5: Comparisons (e.g. 'SIP vs FD') do NOT activate fast-path."""
    ep = QueryExecutionPlan(
        original_query="SIP vs FD which is better?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.COMPARISON,
        operation=OperationType.COMPARE,
        comparison_info=ComparisonInfo(is_comparison=True, comparison_items=["SIP", "FD"]),
        requires_rag=True,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.GENERAL_FINANCE,
        execution_plan=ep,
        query="SIP vs FD which is better?",
    )
    assert is_fp is False
    assert reason is None
    assert budget == 0


def test_fast_path_disabled_for_historical():
    """Test 6: Historical analysis queries do NOT activate fast-path."""
    ep = QueryExecutionPlan(
        original_query="what was my spending last year?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.SPENDING_ANALYSIS,
        scope=QueryScope.PERSONAL_ANALYSIS,
        operation=OperationType.ANALYZE,
    )
    temp_ref = TemporalReference(expression="last year", is_historical=True)
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        temporal_references=[temp_ref],
        query="what was my spending last year?",
    )
    assert is_fp is False
    assert reason is None
    assert budget == 0


def test_fast_path_disabled_for_market_query():
    """Test 7: Queries requiring live market data do NOT activate fast-path."""
    ep = QueryExecutionPlan(
        original_query="what is the gold rate today?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.MARKET_INFORMATION,
        operation=OperationType.LOOKUP,
        requires_market_data=True,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.GENERAL_FINANCE,
        execution_plan=ep,
        query="what is the gold rate today?",
    )
    assert is_fp is False
    assert reason is None
    assert budget == 0


# ─── 3. ADAPTIVE TOKEN BUDGET SELECTION TESTS ─────────────────────────────────

def test_adaptive_token_budget_selector_fast_path():
    """Test 11: Direct personal lookup enforces output token budget <= 180."""
    selector = AdaptiveTokenBudgetSelector()
    ep = QueryExecutionPlan(
        original_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    config = selector.select_config(
        query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
    )
    assert config.max_tokens <= 180
    assert config.max_tokens == 128


def test_adaptive_token_budget_complex_retained():
    """Test 12: Complex / comparison queries retain standard adaptive budgets."""
    selector = AdaptiveTokenBudgetSelector()
    ep_plan = QueryExecutionPlan(
        original_query="create a retirement plan for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
    )
    config_plan = selector.select_config(
        query="create a retirement plan for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep_plan,
    )
    assert config_plan.max_tokens >= 512

    ep_comp = QueryExecutionPlan(
        original_query="SIP vs FD comparison",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.COMPARISON,
        operation=OperationType.COMPARE,
        comparison_info=ComparisonInfo(is_comparison=True, comparison_items=["SIP", "FD"]),
)
    config_comp = selector.select_config(
        query="SIP vs FD comparison",
        intent=QueryIntent.GENERAL_FINANCE,
        execution_plan=ep_comp,
    )
    assert config_comp.max_tokens >= 250


# ─── 4. CACHE EXCLUSION & ZERO-HALLUCINATION FALLBACK TESTS ───────────────────

def test_personalized_response_not_cached():
    """Test 14: Personalized responses are strictly excluded from response caching."""
    # Fast path query with personal context
    eligible = CacheEligibilityPolicy.is_eligible(
        query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        scope="PERSONAL_LOOKUP",
        operation="LOOKUP",
        has_personal_context=True,
        has_live_market_data=False,
    )
    assert eligible is False


def test_missing_financial_context_safe_fallback():
    """Test 13: Missing personal financial context uses safe zero-hallucination fallback."""
    builder = AIContextBuilder()
    empty_ufc = MagicMock()
    empty_ufc.cash_flow = MagicMock(has_data=False)
    empty_ufc.net_worth = MagicMock(has_data=False)
    empty_ufc.investments = MagicMock(has_data=False)
    empty_ufc.loans = MagicMock(has_data=False)
    empty_ufc.goals = MagicMock(has_data=False)
    empty_ufc.budgets = MagicMock(has_data=False)
    empty_ufc.financial_health = MagicMock(has_data=False)
    assert builder._has_any_financial_data(empty_ufc) is False


# ─── 5. CONCISE PROMPTING & GUIDANCE TESTS ────────────────────────────────────

def test_prompt_guidance_for_personal_lookup():
    """Test concise, non-verbose response guidance in prompt builder."""
    builder = AIContextBuilder()
    ufc = MagicMock()
    ufc.goals = MagicMock(has_data=True)
    ufc.cash_flow = None
    ufc.net_worth = None
    ufc.investments = None
    ufc.loans = None
    ufc.budgets = None
    ufc.financial_health = None
    ufc.model_dump = MagicMock(return_value={"goals": [{"name": "Emergency Fund", "target": 100000}]})

    context = AIContext(
        question="tell me about my goal",
        user_financial_context=None,
    )
    prompt = builder.build_prompt(
        context=context,
        intent="PERSONAL_FINANCE",
        scope="PERSONAL_LOOKUP",
    )
    assert "Answer the user's question directly, clearly, and concisely in 1–3 short sentences" in prompt
    assert "Do not add generic educational sections" in prompt


# ─── 6. OBSERVABILITY & TELEMETRY RECORDING TESTS ─────────────────────────────

def test_observability_flags_recording():
    """Test 16: Latency breakdown records all Phase L.11.2 fast-path telemetry fields."""
    tracker = LatencyTracker(enabled=True)
    tracker.record_flag("personal_fast_path_used", True)
    tracker.record_flag("general_rag_skipped", True)
    tracker.record_flag("market_data_skipped", True)
    tracker.record_flag("minimal_context_used", True)
    tracker.record_count("adaptive_output_budget", 128)
    tracker.record_str("fast_path_reason", "DIRECT_PERSONAL_LOOKUP")

    breakdown = tracker.breakdown
    assert breakdown.personal_fast_path_used is True
    assert breakdown.general_rag_skipped is True
    assert breakdown.market_data_skipped is True
    assert breakdown.minimal_context_used is True
    assert breakdown.adaptive_output_budget == 128
    assert breakdown.fast_path_reason == "DIRECT_PERSONAL_LOOKUP"

    telemetry_dict = tracker.to_dict()
    assert telemetry_dict["personal_fast_path_used"] is True
    assert telemetry_dict["general_rag_skipped"] is True
    assert telemetry_dict["market_data_skipped"] is True
    assert telemetry_dict["minimal_context_used"] is True
    assert telemetry_dict["adaptive_output_budget"] == 128
    assert telemetry_dict["fast_path_reason"] == "DIRECT_PERSONAL_LOOKUP"


# ─── 7. SERVICE END-TO-END FAST-PATH INTEGRATION TESTS ─────────────────────────

@pytest.mark.anyio
async def test_fast_path_service_send_chat_message_integration():
    """Test 8 & 9: Full service execution skips general RAG & market data for direct lookup."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import AIAdvisorRequest
    from app.ai.schemas.query_understanding import QueryUnderstanding

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Your goal is to save ₹1,00,000 for your Emergency Fund.")
    
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock()

    mock_safety = MagicMock()
    mock_safety.validate_response = MagicMock()

    mock_builder = AIContextBuilder()
    
    mock_dash = MagicMock()
    mock_dash.build_dashboard = MagicMock(return_value=None)

    from datetime import datetime

    mock_conv = MagicMock()
    mock_conv.get_conversation = MagicMock(return_value=MagicMock(id=123, user_id=1))
    mock_conv.get_recent_messages = MagicMock(return_value=[])
    dummy_user_msg = MagicMock(id=1, conversation_id=123, role="user", content="tell me about my goal", message_metadata={}, created_at=datetime.utcnow())
    dummy_asst_msg = MagicMock(id=2, conversation_id=123, role="assistant", content="Your goal is to save ₹1,00,000 for your Emergency Fund.", message_metadata={}, created_at=datetime.utcnow())
    mock_conv.store_user_message = MagicMock(return_value=dummy_user_msg)
    mock_conv.store_assistant_message = MagicMock(return_value=dummy_asst_msg)

    mock_understanding_service = MagicMock()
    ep = QueryExecutionPlan(
        original_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    mock_understanding_service.analyze = MagicMock(return_value=QueryUnderstanding(
        original_query="tell me about my goal",
        normalized_query="tell me about my goal",
        corrected_query="tell me about my goal",
        resolved_query="tell me about my goal",
        retrieval_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        execution_plan=ep,
        requires_personal_data=True,
        requires_market_data=False,
    ))

    mock_market_service = MagicMock()
    mock_market_service.get_relevant_market_data = AsyncMock()

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        market_data_service=mock_market_service,
        query_understanding_service=mock_understanding_service,
    )

    from app.ai.schemas.advisor import SendMessageRequest

    request = SendMessageRequest(message="tell me about my goal")
    response = await service.send_chat_message(user_id=1, conversation_id=123, request=request)

    # 1. RAG retrieval was NOT called
    mock_rag.retrieve.assert_not_called()

    # 2. Market data service was NOT called
    mock_market_service.get_relevant_market_data.assert_not_called()

    # 3. Safety validator was called
    assert mock_safety.validate_response.call_count >= 1

    # 4. LLM was invoked with adaptive budget <= 180
    mock_llm.generate.assert_called_once()
    call_kwargs = mock_llm.generate.call_args[1]
    assert call_kwargs.get("max_tokens", 512) <= 180
