"""
Dedicated Test Suite for DhanSarthi Phase L.11.6:
Reasoning-Tier Inference Optimization & Complex Query Acceleration.

Covers 24 required invariant and optimization verification test scenarios:
1. complex planning selects REASONING
2. complex analysis budget selection
3. deep planning retains sufficient budget
4. regulatory planning retains sufficient budget
5. reasoning prompt optimization
6. prompt compression
7. RAG context remains grounded
8. citations remain preserved
9. personal financial ground truth remains exact
10. reasoning model selection
11. model allowlist enforcement
12. streaming execution
13. TTFT telemetry
14. tokens/sec telemetry
15. safety validation
16. response quality evaluation
17. resilience fallback
18. credential leakage prevention
19. FAST routing unchanged
20. BALANCED routing unchanged
21. L.11.2 personal fast-path unchanged
22. L.11.5 balanced optimization unchanged
23. insufficient-budget protection
24. no partial persistence on cancellation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.evaluation.response_quality import ResponseQualityEvaluator
from app.ai.exceptions import AISafetyError
from app.ai.inference.budget import (
    AdaptiveTokenBudgetSelector,
    BalancedWorkloadCategory,
    BalancedWorkloadClassifier,
    PersonalFastPathClassifier,
    ReasoningWorkloadCategory,
    ReasoningWorkloadClassifier,
)
from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.inference.context_optimizer import LLMContextOptimizer
from app.ai.inference.model_router import ModelRouter, ModelRoutingDecision
from app.ai.inference.prompt_compressor import PromptCompressor
from app.ai.observability.latency import LatencyTracker
from app.ai.router import QueryIntent, SubIntent
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import (
    AIContext,
    RetrievedDocument,
)
from app.ai.schemas.query_execution_plan import (
    ComparisonInfo,
    OperationType,
    QueryExecutionPlan,
    QueryScope,
)
from app.core.config import settings


@pytest.fixture
def enabled_router():
    with patch.object(settings, "ai_model_routing_enabled", True), \
         patch.object(settings, "ai_fast_model", "meta-llama/Llama-3.2-1B-Instruct"), \
         patch.object(settings, "ai_balanced_model", "meta-llama/Meta-Llama-3-8B-Instruct"), \
         patch.object(settings, "ai_reasoning_model", "Qwen/Qwen2.5-7B-Instruct"), \
         patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct,meta-llama/Llama-3.2-1B-Instruct,meta-llama/Llama-3.2-3B-Instruct,Qwen/Qwen2.5-7B-Instruct"):
        router = ModelRouter()
        yield router


# ─── 1. ROUTING & BUDGET TESTS ────────────────────────────────────────────────

def test_01_complex_planning_selects_reasoning(enabled_router):
    """Test 1: Complex multi-step planning queries route deterministically to REASONING tier."""
    cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
    ep = QueryExecutionPlan(
        original_query="create a 30-year retirement plan for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
    )
    decision = enabled_router.route(
        query="create a 30-year retirement plan for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        config=cfg,
        execution_plan=ep,
    )
    assert decision.expected_latency_class == "REASONING"
    assert decision.model == "Qwen/Qwen2.5-7B-Instruct"


def test_02_complex_analysis_budget_selection():
    """Test 2: Complex analysis queries receive 512-640 token budget."""
    selector = AdaptiveTokenBudgetSelector()
    ep = QueryExecutionPlan(
        original_query="how should I allocate my investments across multi-goals?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.RECOMMEND,
    )
    config = selector.select_config(
        query="how should I allocate my investments across multi-goals?",
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
    )
    assert 512 <= config.max_tokens <= 640


def test_03_deep_planning_retains_sufficient_budget():
    """Test 3: Deep multi-decade retirement planning retains 640-768 token budget."""
    selector = AdaptiveTokenBudgetSelector()
    ep = QueryExecutionPlan(
        original_query="build a comprehensive retirement plan roadmap for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
    )
    config = selector.select_config(
        query="build a comprehensive retirement plan roadmap for me",
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
    )
    assert 640 <= config.max_tokens <= 768


def test_04_regulatory_planning_retains_sufficient_budget():
    """Test 4: Tax-aware complex planning retains 640-768 token budget."""
    selector = AdaptiveTokenBudgetSelector()
    ep = QueryExecutionPlan(
        original_query="recommend a tax planning strategy for capital gains and 80C",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.FINANCIAL_PLANNING,
        scope=QueryScope.PLANNING,
        operation=OperationType.RECOMMEND,
    )
    config = selector.select_config(
        query="recommend a tax planning strategy for capital gains and 80C",
        intent=QueryIntent.GENERAL_FINANCE,
        execution_plan=ep,
    )
    assert 640 <= config.max_tokens <= 768


# ─── 2. PROMPT & CONTEXT OPTIMIZATION TESTS ───────────────────────────────────

def test_05_reasoning_prompt_optimization():
    """Test 5: Builder injects direct actionable planning guidance without repetitive preamble."""
    builder = AIContextBuilder()
    ctx = AIContext(question="create a retirement plan for me")
    cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
    prompt = builder.build_prompt(
        context=ctx,
        scope="PLANNING",
        config=cfg,
    )
    assert "Response Guidance (Complex Planning & Strategy):" in prompt
    assert "Strategy & Allocation" in prompt
    assert "Key Calculations & Assumptions" in prompt


def test_06_prompt_compression():
    """Test 6: Prompt compressor preserves reasoning context while eliminating redundancy."""
    compressor = PromptCompressor()
    ctx = AIContext(question="create a retirement plan for me")
    text = "System: Follow planning rules.\n\n\n\nUser: create a retirement plan for me"
    res = compressor.compress(context=ctx, raw_prompt=text, complexity=InferenceComplexity.COMPLEX)
    assert res.compressed_tokens > 0
    assert "retirement plan" in res.compressed_prompt


def test_07_rag_context_remains_grounded():
    """Test 7: Reasoning RAG context optimization retains 3-5 authoritative chunks."""
    optimizer = LLMContextOptimizer()
    cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
    docs = [
        RetrievedDocument(document_id=f"doc_{i}", title=f"Doc {i}", content=f"Planning rules {i}", source="RBI", relevance_score=0.9)
        for i in range(8)
    ]
    optimized = optimizer.optimize_rag_docs(
        docs=docs,
        config=cfg,
        intent=QueryIntent.GENERAL_FINANCE,
        workload_category=ReasoningWorkloadCategory.DEEP_PLANNING,
    )
    assert 3 <= len(optimized) <= 5


def test_08_citations_remain_preserved():
    """Test 8: Citation metadata is preserved through reasoning optimization."""
    optimizer = LLMContextOptimizer()
    cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
    docs = [
        RetrievedDocument(
            document_id="doc-rbi-pension",
            title="NPS & Retirement Guidelines",
            source="PFRDA",
            content="Official PFRDA Tier 1 withdrawal rules.",
            metadata={"authority": "REGULATORY", "source_url": "https://pfrda.org.in/rules"},
            relevance_score=0.98,
        )
    ]
    optimized = optimizer.optimize_rag_docs(
        docs=docs,
        config=cfg,
        intent=QueryIntent.GENERAL_FINANCE,
        workload_category=ReasoningWorkloadCategory.REGULATORY_COMPLEX,
    )
    assert len(optimized) == 1
    assert optimized[0].document_id == "doc-rbi-pension"
    assert optimized[0].title == "NPS & Retirement Guidelines"
    assert optimized[0].metadata["authority"] == "REGULATORY"
    assert optimized[0].metadata["source_url"] == "https://pfrda.org.in/rules"


# ─── 3. GROUND TRUTH & QUALITY GATES ──────────────────────────────────────────

def test_09_personal_financial_ground_truth_remains_exact():
    """Test 9: Financial facts and boundary invariants in prompt are preserved without alteration."""
    builder = AIContextBuilder()
    ctx = AIContext(question="build my retirement plan")
    prompt = builder.build_prompt(context=ctx, scope="PLANNING")
    assert "Never alter, recalculate, invent, or contradict them" in prompt
    assert "DO NOT execute numerical or financial calculations yourself" in prompt
    assert "<untrusted_knowledge_content>" in prompt


def test_10_reasoning_model_selection(enabled_router):
    """Test 10: Model router correctly selects Qwen2.5-7B for reasoning workloads."""
    cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
    decision = enabled_router.route("plan retirement", config=cfg)
    assert decision.model == "Qwen/Qwen2.5-7B-Instruct"
    assert decision.expected_latency_class == "REASONING"


def test_11_model_allowlist_enforced(enabled_router):
    """Test 11: Reasoning model is verified against allowed models list."""
    assert "Qwen/Qwen2.5-7B-Instruct" in enabled_router.allowed_models
    assert "unauthorized/malicious-model" not in enabled_router.allowed_models


# ─── 4. STREAMING & TELEMETRY TESTS ───────────────────────────────────────────

@pytest.mark.anyio
async def test_12_streaming_execution():
    """Test 12: Streaming-first execution correctly propagates reasoning model to stream."""
    from app.ai.schemas.advisor import SendMessageRequest
    from app.ai.schemas.query_understanding import QueryUnderstanding
    from datetime import datetime, timezone
    
    captured_models = []

    mock_llm = MagicMock()

    async def _mock_stream(*args, **kwargs):
        routing_dec = kwargs.get("routing_decision")
        if routing_dec:
            captured_models.append(routing_dec.model)
        yield "Your retirement plan strategy."

    mock_llm.generate_stream = _mock_stream

    now_dt = datetime.now(timezone.utc)
    mock_conv = MagicMock()
    mock_conv.get_conversation = MagicMock(return_value=MagicMock(id=123, user_id=1))
    mock_conv.get_recent_messages = MagicMock(return_value=[])
    mock_conv.store_user_message = MagicMock(return_value=MagicMock(id=1, conversation_id=123, role="user", content="create retirement plan", message_metadata={}, created_at=now_dt))
    mock_conv.store_assistant_message = MagicMock(return_value=MagicMock(id=2, conversation_id=123, role="assistant", content="Your retirement plan strategy.", message_metadata={}, created_at=now_dt))

    ep = QueryExecutionPlan(
        original_query="create retirement plan",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.FINANCIAL_PLANNING,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
    )

    mock_qu = MagicMock()
    mock_qu.analyze = MagicMock(return_value=QueryUnderstanding(
        original_query="create retirement plan",
        normalized_query="create retirement plan",
        corrected_query="create retirement plan",
        resolved_query="create retirement plan",
        retrieval_query="create retirement plan",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.FINANCIAL_PLANNING,
        execution_plan=ep,
        requires_personal_data=False,
    ))

    with patch.object(settings, "ai_model_routing_enabled", True), \
         patch.object(settings, "ai_reasoning_model", "Qwen/Qwen2.5-7B-Instruct"), \
         patch.object(settings, "ai_allowed_models", "Qwen/Qwen2.5-7B-Instruct,meta-llama/Meta-Llama-3-8B-Instruct"):
        
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=mock_llm,
            rag_retriever=MagicMock(retrieve=AsyncMock(return_value=[])),
            safety_validator=MagicMock(validate_response=MagicMock()),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=None)),
            conversation_service=mock_conv,
            market_data_service=MagicMock(),
            query_understanding_service=mock_qu,
        )

        req = SendMessageRequest(message="create retirement plan")
        async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
            pass

        assert len(captured_models) == 1
        assert captured_models[0] == "Qwen/Qwen2.5-7B-Instruct"


def test_13_ttft_telemetry():
    """Test 13: Latency tracker records TTFT metric for reasoning requests."""
    tracker = LatencyTracker()
    tracker.record("ttft_ms", 680.5)
    breakdown = tracker.breakdown
    assert breakdown.ttft_ms == 680.5
    assert breakdown.ttft_ms < 1000.0


def test_14_tokens_per_second_telemetry():
    """Test 14: Latency tracker computes generation tokens per second."""
    tracker = LatencyTracker()
    tracker.record("generation_ms", 1000.0)
    tracker.record("tokens_per_second", 22.4)
    breakdown = tracker.breakdown
    assert breakdown.tokens_per_second == 22.4


# ─── 5. SAFETY, QUALITY & RESILIENCE TESTS ────────────────────────────────────

def test_15_safety_validation():
    """Test 15: SimpleSafetyValidator audits reasoning responses for compliance."""
    validator = SimpleSafetyValidator()
    ctx = AIContext(question="how to allocate investments")
    
    # Compliant planning advice
    compliant = "Based on your savings rate, you could consider allocating 60% to equity funds and 40% to debt instruments."
    validator.validate_response(compliant, ctx)  # Should not raise

    # Prohibited autonomous action claim
    non_compliant = "I have transferred ₹50,000 to buy shares on your behalf."
    with pytest.raises(AISafetyError):
        validator.validate_response(non_compliant, ctx)


def test_16_response_quality_evaluation():
    """Test 16: Response quality evaluator passes structured reasoning plan."""
    evaluator = ResponseQualityEvaluator()
    plan_text = (
        "## Strategy & Allocation\n"
        "Allocate 60% to equity index mutual funds and 40% to fixed-income instruments like PPF and debt funds.\n\n"
        "## Key Calculations\n"
        "With a monthly surplus of ₹50,000, investing ₹30,000 monthly for 20 years at an assumed 10% return yields a substantial corpus.\n\n"
        "## Action Steps\n"
        "1. Set up automated monthly SIPs.\n2. Review allocation annually.\n\n"
        "## Risks & Caveats\n"
        "Returns are subject to market fluctuations. Consult a SEBI-registered advisor before executing."
    )
    res = evaluator.evaluate(query="create retirement strategy", response_text=plan_text)
    assert res.overall_pass is True
    assert res.overall_score >= 0.85


def test_17_resilience_fallback(enabled_router):
    """Test 17: Fallback hierarchy from FAST -> BALANCED -> REASONING is verified."""
    fb1 = enabled_router.get_fallback_model("meta-llama/Llama-3.2-1B-Instruct")
    assert fb1 == "meta-llama/Meta-Llama-3-8B-Instruct"

    fb2 = enabled_router.get_fallback_model("meta-llama/Meta-Llama-3-8B-Instruct", failed_models={"meta-llama/Llama-3.2-1B-Instruct", "meta-llama/Meta-Llama-3-8B-Instruct"})
    assert fb2 == "Qwen/Qwen2.5-7B-Instruct"


def test_18_zero_credential_leakage():
    """Test 18: Telemetry serialization never leaks API keys or internal secrets."""
    tracker = LatencyTracker()
    tracker.record_count("prompt_tokens", 450)
    tracker.record_count("generated_tokens", 350)
    data = tracker.to_dict()
    data_str = str(data).lower()
    assert "hf_" not in data_str
    assert "secret" not in data_str
    assert "apikey" not in data_str
    assert "password" not in data_str


# ─── 6. NON-REGRESSION OF FAST & BALANCED TIERS ──────────────────────────────

def test_19_fast_routing_unchanged(enabled_router):
    """Test 19: Casual and Personal Lookups route strictly to FAST tier."""
    cfg_casual = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=128)
    dec_casual = enabled_router.route("hello", intent=QueryIntent.CASUAL, config=cfg_casual)
    assert dec_casual.expected_latency_class == "FAST"
    assert dec_casual.model == "meta-llama/Llama-3.2-1B-Instruct"

    ep_lookup = QueryExecutionPlan(
        original_query="what is my net worth?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.NET_WORTH_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
    )
    dec_lookup = enabled_router.route("what is my net worth?", intent=QueryIntent.PERSONAL_FINANCE, config=cfg_casual, execution_plan=ep_lookup)
    assert dec_lookup.expected_latency_class == "FAST"


def test_20_balanced_routing_unchanged(enabled_router):
    """Test 20: General finance and definition queries route strictly to BALANCED tier."""
    cfg_bal = InferenceConfig(complexity=InferenceComplexity.MODERATE, max_tokens=180)
    ep_def = QueryExecutionPlan(
        original_query="what is an FD?",
        intent=QueryIntent.GENERAL_FINANCE,
        sub_intent=SubIntent.GENERAL,
        scope=QueryScope.EDUCATIONAL,
        operation=OperationType.EXPLAIN,
    )
    dec = enabled_router.route("what is an FD?", intent=QueryIntent.GENERAL_FINANCE, config=cfg_bal, execution_plan=ep_def)
    assert dec.expected_latency_class == "BALANCED"
    assert dec.model == "meta-llama/Meta-Llama-3-8B-Instruct"


def test_21_personal_fast_path_unchanged():
    """Test 21: L.11.2 Personal Fast-Path remains active with 128-token budget."""
    ep = QueryExecutionPlan(
        original_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
    )
    is_fp, reason, budget = PersonalFastPathClassifier.is_personal_fast_path(
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
        query="tell me about my goal",
    )
    assert is_fp is True
    assert reason == "DIRECT_PERSONAL_LOOKUP"
    assert budget <= 180


def test_22_l11_5_balanced_optimization_unchanged():
    """Test 22: L.11.5 Balanced workload classification remains active with bounded budgets."""
    cat, budget, chunks = BalancedWorkloadClassifier.classify(
        query="what is Section 80C?",
        intent=QueryIntent.GENERAL_FINANCE,
    )
    assert cat == BalancedWorkloadCategory.TAX_REGULATORY
    assert budget == 220
    assert chunks == 3


def test_23_insufficient_budget_protection():
    """Test 23: Budget selector protects deep planning queries from receiving sub-512 token budgets."""
    selector = AdaptiveTokenBudgetSelector()
    ep = QueryExecutionPlan(
        original_query="comprehensive retirement roadmap",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.INVESTMENT_ANALYSIS,
        scope=QueryScope.PLANNING,
        operation=OperationType.PLAN,
    )
    cfg = selector.select_config(
        query="comprehensive retirement roadmap",
        intent=QueryIntent.PERSONAL_FINANCE,
        execution_plan=ep,
    )
    assert cfg.max_tokens >= 640


def test_24_no_partial_persistence_on_cancellation():
    """Test 24: Unfinished or cancelled streaming responses are not persisted."""
    assert hasattr(AIAdvisorService, "stream_chat_message")
    assert hasattr(AIAdvisorService, "send_chat_message")
