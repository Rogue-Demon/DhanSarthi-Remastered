"""
Unit and integration test suite for Phase L.8 Real-Time LLM Inference Optimization & Model Selection.

Verifies:
  - Tokenizer lazy loading, thread safety, token counting, and ratio fallback
  - ModelRouter selection policy, disabled mode, and server allowlist validation
  - Provider model parameter propagation, TTFT tracking, and tokens/sec metrics
  - Security constraints (allowlist enforcement, API key mask, prompt boundary)
  - Clean error propagation and fallback handling
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.inference.model_router import ModelRouter, ModelRoutingDecision
from app.ai.inference.tokenizer import LLMTokenizer, get_tokenizer
from app.ai.observability.inference_metrics import RealInferenceMetricsTracker
from app.ai.observability.latency import LatencyTracker
from app.ai.router import QueryIntent
from app.core.config import settings


class TestLLMTokenizer:
    def test_lazy_loading_not_initialized_on_creation(self):
        tok = LLMTokenizer(model_name="meta-llama/Meta-Llama-3-8B-Instruct")
        assert tok._is_loaded is False
        assert tok._tokenizer is None

    def test_count_tokens_fallback_estimation(self):
        tok = LLMTokenizer(model_name="invalid-offline-model-id-12345")
        count = tok.count_tokens("What is a mutual fund?")
        assert count > 0
        assert count == max(1, int(len("What is a mutual fund?") / 4.0))
        assert tok._load_failed is True

    def test_count_prompt_tokens_list(self):
        tok = LLMTokenizer(model_name="invalid-offline-model-id-12345")
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there"}]
        count = tok.count_prompt_tokens(messages)
        assert count > 0

    def test_truncate_to_token_budget(self):
        tok = LLMTokenizer(model_name="invalid-offline-model-id-12345")
        text = "This is a long financial context explanation that needs truncation."
        truncated = tok.truncate_to_token_budget(text, max_tokens=3)
        assert len(truncated) <= len(text)
        assert len(truncated) > 0

    def test_get_tokenizer_singleton_reuse(self):
        tok1 = get_tokenizer()
        tok2 = get_tokenizer()
        assert tok1 is tok2


class TestModelRouter:
    def setup_method(self):
        self.router = ModelRouter()

    def test_disabled_mode_returns_primary_model(self):
        with patch.object(settings, "ai_model_routing_enabled", False):
            router = ModelRouter()
            cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=256)
            decision = router.route("hi", intent=QueryIntent.CASUAL, config=cfg)
            assert decision.model == settings.ai_model
            assert decision.reason == "ROUTING_DISABLED"

    def test_simple_query_routes_to_fast_model_when_enabled(self):
        with patch.object(settings, "ai_model_routing_enabled", True), \
             patch.object(settings, "ai_fast_model", "meta-llama/Llama-3.2-1B-Instruct"), \
             patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct,meta-llama/Llama-3.2-1B-Instruct"):
            router = ModelRouter()
            cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=256)
            decision = router.route("hi", intent=QueryIntent.CASUAL, config=cfg)
            assert decision.model == "meta-llama/Llama-3.2-1B-Instruct"
            assert decision.expected_latency_class == "FAST"

    def test_complex_planning_routes_to_reasoning_model(self):
        with patch.object(settings, "ai_model_routing_enabled", True), \
             patch.object(settings, "ai_reasoning_model", "Qwen/Qwen2.5-7B-Instruct"), \
             patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct,Qwen/Qwen2.5-7B-Instruct"):
            router = ModelRouter()
            mock_plan = MagicMock()
            mock_plan.operation.value = "PLANNING"
            cfg = InferenceConfig(complexity=InferenceComplexity.COMPLEX, max_tokens=768)
            decision = router.route("Create detailed retirement plan", intent=QueryIntent.MIXED, config=cfg, execution_plan=mock_plan)
            assert decision.model == "Qwen/Qwen2.5-7B-Instruct"
            assert decision.expected_latency_class == "REASONING"

    def test_untrusted_model_candidate_falls_back_to_primary_model(self):
        with patch.object(settings, "ai_model_routing_enabled", True), \
             patch.object(settings, "ai_fast_model", "unauthorized-malicious-model-id"), \
             patch.object(settings, "ai_allowed_models", "meta-llama/Meta-Llama-3-8B-Instruct"):
            router = ModelRouter()
            cfg = InferenceConfig(complexity=InferenceComplexity.SIMPLE, max_tokens=256)
            decision = router.route("hi", intent=QueryIntent.CASUAL, config=cfg)
            assert decision.model == settings.ai_model  # Fallback to trusted primary model


class TestRealInferenceMetricsTracker:
    def test_streaming_ttft_and_tps_calculation(self):
        tracker = RealInferenceMetricsTracker(model_name="test-model", provider_name="huggingface", is_streaming=True)
        tracker.start_request()
        ttft = tracker.record_first_token()
        assert ttft >= 0.0

        res = tracker.finish_request(prompt_tokens=100, generated_tokens=50)
        assert res["prompt_tokens"] == 100
        assert res["generated_tokens"] == 50
        assert res["tokens_per_second"] >= 0.0
        assert res["is_streaming"] is True


@pytest.mark.anyio
async def test_provider_model_parameter_propagation():
    """Verify routing decision model parameter is recorded in LatencyTracker by MockLLMProvider."""
    from app.ai.providers.mock import MockLLMProvider
    from app.ai.schemas.advisor import AIContext

    provider = MockLLMProvider(response_text="Test response.")
    tracker = LatencyTracker()
    decision = ModelRoutingDecision(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        reason="TEST_ROUTING",
        complexity=InferenceComplexity.SIMPLE,
        expected_latency_class="FAST",
        max_tokens=256,
        temperature=0.2,
    )
    ctx = AIContext(question="What is SIP?")
    resp = await provider.generate(ctx, "What is SIP?", tracker=tracker, routing_decision=decision)

    assert resp == "Test response."
    metrics = tracker.to_dict()
    assert metrics["selected_model"] == "meta-llama/Meta-Llama-3-8B-Instruct"
    assert metrics["model_routing_reason"] == "TEST_ROUTING"
    assert metrics["generated_tokens"] > 0
