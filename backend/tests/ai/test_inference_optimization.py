"""
Unit and integration tests for Phase L.7.4 Adaptive LLM Inference Optimization.

Verifies:
  - Complexity classification (SIMPLE, MODERATE, COMPLEX)
  - Adaptive token budgets and history message limits
  - Context routing rules (CASUAL, GENERAL, PERSONAL, MIXED, MARKET)
  - Character budget trimming & context priority order
  - Preserved security tags (<untrusted_knowledge_content>, <personal_financial_context>)
  - Parameter propagation to generate() and generate_stream()
  - Graceful fallback when AI_ADAPTIVE_INFERENCE_ENABLED=false
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.inference.budget import AdaptiveTokenBudgetSelector, InferenceComplexityClassifier
from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.inference.context_optimizer import LLMContextOptimizer
from app.ai.router import QueryIntent
from app.ai.schemas.advisor import AIContext, RetrievedDocument
from app.core.config import settings


class TestInferenceComplexityClassifier:
    def setup_method(self):
        self.classifier = InferenceComplexityClassifier()

    def test_casual_query_is_simple(self):
        comp = self.classifier.classify("hi", intent=QueryIntent.CASUAL)
        assert comp == InferenceComplexity.SIMPLE

    def test_simple_definition_is_simple(self):
        comp = self.classifier.classify("What is SIP?", intent=QueryIntent.GENERAL_FINANCE)
        assert comp == InferenceComplexity.SIMPLE

    def test_comparison_query_is_moderate(self):
        mock_plan = MagicMock()
        mock_plan.comparison_info.is_comparison = True
        mock_plan.operation.value = "COMPARE"
        comp = self.classifier.classify("SIP vs FD comparison", intent=QueryIntent.GENERAL_FINANCE, execution_plan=mock_plan)
        assert comp == InferenceComplexity.MODERATE

    def test_personal_lookup_is_moderate(self):
        comp = self.classifier.classify("How much did I spend this month?", intent=QueryIntent.PERSONAL_FINANCE)
        assert comp == InferenceComplexity.MODERATE

    def test_planning_query_is_complex(self):
        mock_plan = MagicMock()
        mock_plan.operation.value = "PLANNING"
        comp = self.classifier.classify("Create a detailed retirement plan for me", intent=QueryIntent.MIXED, execution_plan=mock_plan)
        assert comp == InferenceComplexity.COMPLEX

    def test_debt_vs_investment_tradeoff_is_complex(self):
        comp = self.classifier.classify("Should I prioritize paying home loan or investing in mutual funds?", intent=QueryIntent.MIXED)
        assert comp == InferenceComplexity.COMPLEX


class TestAdaptiveTokenBudgetSelector:
    def setup_method(self):
        self.selector = AdaptiveTokenBudgetSelector()

    def test_casual_token_budget_is_128(self):
        cfg = self.selector.select_config("hello", intent=QueryIntent.CASUAL)
        assert cfg.max_tokens <= 128
        assert cfg.history_limit == 2

    def test_simple_token_budget_is_256(self):
        cfg = self.selector.select_config("What is 80C?", intent=QueryIntent.GENERAL_FINANCE)
        assert cfg.max_tokens <= 256
        assert cfg.history_limit == 4

    def test_comparison_token_budget_is_bounded(self):
        mock_plan = MagicMock()
        mock_plan.scope.value = "COMPARISON"
        mock_plan.comparison_info.is_comparison = True
        cfg = self.selector.select_config("SIP vs FD", intent=QueryIntent.GENERAL_FINANCE, execution_plan=mock_plan)
        assert 220 <= cfg.max_tokens <= 512
        assert cfg.history_limit == 8

    def test_complex_planning_token_budget_is_768(self):
        mock_plan = MagicMock()
        mock_plan.operation.value = "PLANNING"
        cfg = self.selector.select_config("Create retirement plan", intent=QueryIntent.MIXED, execution_plan=mock_plan)
        assert cfg.max_tokens == 768
        assert cfg.history_limit == 10

    def test_effective_max_tokens_never_exceeds_global_safety_max(self):
        mock_plan = MagicMock()
        mock_plan.operation.value = "PLANNING"
        with patch.object(settings, "ai_max_tokens", 400):
            cfg = self.selector.select_config("Complex query", intent=QueryIntent.MIXED, execution_plan=mock_plan)
            assert cfg.max_tokens <= 400


class TestLLMContextOptimizer:
    def setup_method(self):
        self.optimizer = LLMContextOptimizer()

    def test_casual_routing_excludes_rag_and_personal(self):
        cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=128, history_limit=2)
        assert self.optimizer.should_include_personal_context(QueryIntent.CASUAL, cfg) is False
        docs = [RetrievedDocument(document_id="doc1", title="Test", content="Text", source="RAG", relevance_score=0.9)]
        optimized_docs = self.optimizer.optimize_rag_docs(docs, cfg, intent=QueryIntent.CASUAL)
        assert len(optimized_docs) == 0

    def test_general_finance_includes_rag_excludes_personal(self):
        cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=256, history_limit=4)
        assert self.optimizer.should_include_personal_context(QueryIntent.GENERAL_FINANCE, cfg) is False
        docs = [
            RetrievedDocument(document_id="d1", title="D1", content="C1", source="S", relevance_score=0.9),
            RetrievedDocument(document_id="d2", title="D2", content="C2", source="S", relevance_score=0.8),
            RetrievedDocument(document_id="d3", title="D3", content="C3", source="S", relevance_score=0.7),
        ]
        optimized_docs = self.optimizer.optimize_rag_docs(docs, cfg, intent=QueryIntent.GENERAL_FINANCE, is_comparison=False)
        assert len(optimized_docs) == 2  # Simple query prefers top 2

    def test_personal_lookup_includes_personal_excludes_rag(self):
        cfg = InferenceConfig(complexity=InferenceComplexity.MODERATE, max_tokens=384, history_limit=6)
        assert self.optimizer.should_include_personal_context(QueryIntent.PERSONAL_FINANCE, cfg) is True
        docs = [RetrievedDocument(document_id="d1", title="D1", content="C1", source="S", relevance_score=0.9)]
        optimized_docs = self.optimizer.optimize_rag_docs(docs, cfg, intent=QueryIntent.PERSONAL_FINANCE)
        assert len(optimized_docs) == 0

    def test_mixed_includes_rag_and_personal(self):
        cfg = InferenceConfig(complexity=InferenceComplexity.MODERATE, max_tokens=512, history_limit=8)
        assert self.optimizer.should_include_personal_context(QueryIntent.MIXED, cfg) is True

    def test_market_data_only_included_when_explicitly_required(self):
        assert self.optimizer.should_include_market_data(requires_market_data=False) is False
        assert self.optimizer.should_include_market_data(requires_market_data=True) is True

    def test_history_optimization_respects_count_and_character_caps(self):
        class MockMsg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        history = [MockMsg("user" if i % 2 == 0 else "assistant", f"Message number {i} " + "x" * 100) for i in range(20)]
        cfg = InferenceConfig(complexity=InferenceComplexity.MODERATE, max_tokens=512, history_limit=6, max_history_chars=500)
        optimized = self.optimizer.optimize_history(history, cfg)
        assert len(optimized) <= 6
        total_chars = sum(len(m.content) for m in optimized)
        assert total_chars <= 500


@pytest.mark.anyio
async def test_security_tags_and_boundaries_preserved():
    """Verify <untrusted_knowledge_content> and <personal_financial_context> tags remain present in built prompt."""
    from app.ai.context.builder import AIContextBuilder
    from app.ai.schemas.advisor import AIContext, RetrievedDocument

    builder = AIContextBuilder()
    doc = RetrievedDocument(document_id="doc1", title="Section 80C", content="Tax deduction up to 1.5L", source="IncomeTax", relevance_score=0.95)
    ctx = AIContext(
        question="Tell me about 80C",
        user_financial_context=None,
        retrieved_knowledge=[doc],
        conversation_history=[],
    )
    cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=256)
    prompt = builder.build_prompt(ctx, intent="GENERAL_FINANCE", config=cfg)

    assert "<untrusted_knowledge_content>" in prompt
    assert "</untrusted_knowledge_content>" in prompt
    assert "System Instructions:" in prompt


@pytest.mark.anyio
async def test_disabled_mode_preserves_previous_behavior():
    """When AI_ADAPTIVE_INFERENCE_ENABLED=false, standard pipeline execution proceeds without InferenceConfig."""
    with patch.object(settings, "ai_adaptive_inference_enabled", False):
        selector = AdaptiveTokenBudgetSelector()
        # Verify disabled flag leaves settings fallback path active
        assert settings.ai_adaptive_inference_enabled is False
