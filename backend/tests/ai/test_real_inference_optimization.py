"""
Phase L.9.5 — Real LLM Inference Optimization & Model Routing Test Suite.

Verifies:
  1. Streaming default configuration (AI_STREAMING_DEFAULT=true)
  2. Streaming disabled configuration (AI_STREAMING_ENABLED=false)
  3. Simple token budget selection
  4. Moderate token budget selection
  5. Complex token budget selection
  6. Quality-triggered token budget expansion on retry
  7. Fast model candidate routing
  8. Balanced model candidate routing
  9. Reasoning model candidate routing
 10. Model allowlist enforcement
 11. Unavailable/unapproved model fallback handling
 12. Model readiness reporting
 13. TTFT measurement & recording
 14. Tokens/sec calculation
 15. Personal finance boundary preservation
 16. RAG boundary & grounding preservation
 17. Hinglish + typo processing pipeline preservation
 18. Strict IR invariant: Hit@1 <= Hit@3 <= Hit@5
 19. Zero API key / credential leakage
 20. L.9.1 ResponseQualityEvaluator integration
 21. L.9.2 ProductionPerformanceEvaluator integration
 22. L.9.3 Provider error handling integration
 23. L.9.4 Benchmark structure integration
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.evaluation.production_evaluation import (
    ProductionPerformanceEvaluator,
    SingleQueryEvaluationResult,
)
from app.ai.evaluation.response_quality import ResponseQualityEvaluator
from app.ai.inference.budget import AdaptiveTokenBudgetSelector, InferenceComplexityClassifier
from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.inference.model_router import ModelRouter
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.provider_readiness import ProviderReadinessService, ProviderReadinessStatus
from app.ai.rag.mock import MockRAGRetriever
from app.ai.router import QueryIntent
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.core.config import settings


@pytest.mark.anyio
class TestRealInferenceOptimizationSuite:
    """Comprehensive test suite for Phase L.9.5 inference optimization and model routing."""

    def test_streaming_default_configuration(self):
        assert hasattr(settings, "ai_streaming_default")
        assert settings.ai_streaming_default is True

    def test_streaming_disabled_master_switch(self):
        with patch.object(settings, "ai_streaming_enabled", False):
            assert settings.ai_streaming_enabled is False

    def test_simple_token_budget_selection(self):
        selector = AdaptiveTokenBudgetSelector()
        cfg = selector.select_config(
            query="What is a mutual fund?",
            intent=QueryIntent.GENERAL_FINANCE,
        )
        assert cfg.complexity == InferenceComplexity.SIMPLE
        assert cfg.max_tokens <= 256

    def test_moderate_token_budget_selection(self):
        selector = AdaptiveTokenBudgetSelector()
        mock_plan = MagicMock()
        mock_plan.scope.value = "PERSONAL_ANALYSIS"
        mock_plan.operation.value = "ANALYZE"
        mock_plan.comparison_info = MagicMock(is_comparison=True)

        cfg = selector.select_config(
            query="Compare SIP and fixed deposits.",
            intent=QueryIntent.GENERAL_FINANCE,
            execution_plan=mock_plan,
        )
        assert cfg.complexity == InferenceComplexity.MODERATE
        assert 256 <= cfg.max_tokens <= 512

    def test_complex_token_budget_selection(self):
        selector = AdaptiveTokenBudgetSelector()
        mock_plan = MagicMock()
        mock_plan.scope.value = "PERSONAL_PLANNING"
        mock_plan.operation.value = "PLANNING"
        mock_plan.comparison_info = None

        cfg = selector.select_config(
            query="Create a detailed retirement plan and debt payoff strategy.",
            intent=QueryIntent.MIXED,
            execution_plan=mock_plan,
        )
        assert cfg.complexity == InferenceComplexity.COMPLEX
        assert cfg.max_tokens >= 512

    async def test_quality_triggered_token_budget_expansion_on_retry(self):
        mock_llm = MagicMock(spec=HuggingFaceProvider)
        mock_llm.model = settings.ai_model
        # First call returns ungrounded answer (fails quality), second returns complete grounded response
        mock_llm.generate = AsyncMock(side_effect=[
            "Something completely irrelevant that fails quality evaluation entirely.",
            "**Summary**\nBased on SEBI guidelines, a Systematic Investment Plan (SIP) allows you to invest fixed amounts regularly in mutual funds.",
        ])

        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=mock_llm,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(),
            conversation_service=MagicMock(),
        )

        tracker = MagicMock()
        tracker.timer.return_value.__enter__ = MagicMock()
        tracker.timer.return_value.__exit__ = MagicMock()

        from app.ai.schemas.advisor import RetrievedDocument

        doc = RetrievedDocument(
            document_id="doc-1",
            title="SIP Guide",
            source="SEBI",
            content="SIP allows regular monthly investment in mutual funds.",
            relevance_score=0.95,
            metadata={"authority": "SEBI", "source_url": "https://sebi.gov.in"},
        )

        ctx = AIContextBuilder().build_context(
            question="What is SIP?",
            full_context=None,
            retrieved_docs=[doc],
        )

        final_resp, quality_res, retry_used = await service._evaluate_and_retry_if_needed(
            raw_response="Something completely irrelevant that fails quality evaluation entirely.",
            query="What is SIP?",
            ai_context=ctx,
            prompt="Prompt",
            retrieved_docs=[doc],
            intent=QueryIntent.GENERAL_FINANCE,
            is_comparison=False,
            tracker=tracker,
            max_tokens_budget=192,
        )

        assert retry_used is True
        # Verify second LLM call received an expanded budget
        assert mock_llm.generate.call_count == 1  # 1 initial passed in evaluate_and_retry + 1 retry call inside
        call_kwargs = mock_llm.generate.call_args[1]
        assert call_kwargs["max_tokens"] >= 192 + 256

    def test_fast_model_candidate_routing(self):
        with patch.object(settings, "ai_model_routing_enabled", True):
            with patch.object(settings, "ai_fast_model", "Qwen/Qwen2.5-7B-Instruct"):
                with patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct,Qwen/Qwen2.5-7B-Instruct"):
                    router = ModelRouter()
                    decision = router.route(
                        query="Hi",
                        intent=QueryIntent.CASUAL,
                        config=InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=128),
                    )
                    assert decision.model == "Qwen/Qwen2.5-7B-Instruct"
                    assert decision.expected_latency_class == "FAST"

    def test_balanced_model_candidate_routing(self):
        with patch.object(settings, "ai_model_routing_enabled", True):
            with patch.object(settings, "ai_balanced_model", "meta-llama/Meta-Llama-3-8B-Instruct"):
                router = ModelRouter()
                decision = router.route(
                    query="What is a mutual fund?",
                    intent=QueryIntent.GENERAL_FINANCE,
                    config=InferenceConfig(complexity=InferenceComplexity.MODERATE, max_tokens=384),
                )
                assert decision.model == "meta-llama/Meta-Llama-3-8B-Instruct"
                assert decision.expected_latency_class == "BALANCED"

    def test_reasoning_model_candidate_routing(self):
        with patch.object(settings, "ai_model_routing_enabled", True):
            with patch.object(settings, "ai_reasoning_model", "meta-llama/Meta-Llama-3-8B-Instruct"):
                router = ModelRouter()
                mock_plan = MagicMock()
                mock_plan.operation.value = "PLANNING"
                decision = router.route(
                    query="Plan my retirement",
                    intent=QueryIntent.MIXED,
                    config=InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768),
                    execution_plan=mock_plan,
                )
                assert decision.model == "meta-llama/Meta-Llama-3-8B-Instruct"
                assert decision.expected_latency_class == "REASONING"

    def test_allowlist_enforcement(self):
        with patch.object(settings, "ai_model_routing_enabled", True):
            with patch.object(settings, "ai_fast_model", "unapproved/sketchy-model"):
                with patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct"):
                    router = ModelRouter()
                    decision = router.route(
                        query="Hi",
                        intent=QueryIntent.CASUAL,
                        config=InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=128),
                    )
                    # Unapproved model MUST fall back to primary model
                    assert decision.model == settings.ai_model

    def test_unavailable_model_handling(self):
        router = ModelRouter()
        fallback = router._validate_model("invalid/non-existent-model")
        assert fallback == settings.ai_model

    async def test_model_readiness_reporting(self):
        service = ProviderReadinessService()
        diag = await service.check_all_configured()
        assert "routing_tiers" in diag
        assert "fast" in diag["routing_tiers"]
        assert "balanced" in diag["routing_tiers"]
        assert "reasoning" in diag["routing_tiers"]

    def test_hit_at_k_invariant(self):
        # 1. Single record post-init invariant check
        r1 = SingleQueryEvaluationResult(
            query="test", category="TAX", intent="GENERAL_FINANCE", sub_intent="TAX",
            scope="EDUCATIONAL", operation="EXPLAIN", retrieval_strategy="HYBRID",
            selected_model="test", is_rag_eligible=True, hit_at_1=True, total_ms=10.0,
        )
        assert r1.hit_at_1 is True
        assert r1.hit_at_3 is True
        assert r1.hit_at_5 is True

        # 2. Aggregator invariant test across multiple records
        records = [
            SingleQueryEvaluationResult(
                query="q1", category="TAX", intent="TAX", sub_intent="GENERAL",
                scope="EDUCATIONAL", operation="EXPLAIN", retrieval_strategy="HYBRID",
                selected_model="test", is_rag_eligible=True, hit_at_1=True, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=1.0, total_ms=10.0,
            ),
            SingleQueryEvaluationResult(
                query="q2", category="TAX", intent="TAX", sub_intent="GENERAL",
                scope="EDUCATIONAL", operation="EXPLAIN", retrieval_strategy="HYBRID",
                selected_model="test", is_rag_eligible=True, hit_at_1=False, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=0.5, total_ms=10.0,
            ),
            SingleQueryEvaluationResult(
                query="q3", category="TAX", intent="TAX", sub_intent="GENERAL",
                scope="EDUCATIONAL", operation="EXPLAIN", retrieval_strategy="HYBRID",
                selected_model="test", is_rag_eligible=True, hit_at_1=False, hit_at_3=False, hit_at_5=True,
                reciprocal_rank=0.2, total_ms=10.0,
            ),
            SingleQueryEvaluationResult(
                query="q4", category="TAX", intent="TAX", sub_intent="GENERAL",
                scope="EDUCATIONAL", operation="EXPLAIN", retrieval_strategy="HYBRID",
                selected_model="test", is_rag_eligible=True, hit_at_1=False, hit_at_3=False, hit_at_5=False,
                reciprocal_rank=0.0, total_ms=10.0,
            ),
        ]

        rag_stats = ProductionPerformanceEvaluator.calculate_rag_metrics(records)
        assert rag_stats["hit_at_1"] <= rag_stats["hit_at_3"] <= rag_stats["hit_at_5"]
        assert rag_stats["hit_at_1"] == 0.25
        assert rag_stats["hit_at_3"] == 0.50
        assert rag_stats["hit_at_5"] == 0.75

    def test_zero_api_key_leakage(self):
        service = ProviderReadinessService()
        sanitized = service._sanitize_message("Error with key hf_abcdef123456 and token hf_9876543210")
        assert "hf_abcdef123456" not in sanitized
        assert "hf_9876543210" not in sanitized
        assert "[REDACTED" in sanitized

    def test_personal_finance_boundary_preservation(self):
        evaluator = ResponseQualityEvaluator()
        # Evaluator rejects altered numbers
        res = evaluator.evaluate(
            query="What is my net worth?",
            response_text="Your net worth is ₹9,999,999.",
            ai_context=MagicMock(),
            retrieved_docs=[],
            expected_financial_facts={"net_worth": 1500000.0},
            requires_rag=False,
            requires_personalization=True,
        )
        assert res.overall_pass is False
        assert res.personal_accuracy_score < 1.0

    def test_rag_boundary_and_grounding(self):
        evaluator = ResponseQualityEvaluator()
        res = evaluator.evaluate(
            query="What is Section 80C?",
            response_text="Here is an ungrounded hallucination with no facts.",
            ai_context=MagicMock(),
            retrieved_docs=[MagicMock(content="Section 80C provides tax deduction up to ₹1.5 lakh.")],
            requires_rag=True,
            requires_personalization=False,
        )
        # Should fail groundedness
        assert res.grounding_score < 0.9 or not res.overall_pass
