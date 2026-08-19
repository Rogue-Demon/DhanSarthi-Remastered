"""
Mock model providers for unit testing and offline development.
"""

from __future__ import annotations

from typing import Any
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.schemas.advisor import AIContext


class MockLLMProvider(LLMProvider):
    """Generates deterministic mock responses without external network access."""

    def __init__(self, response_text: str = "Mock financial guidance response.") -> None:
        self.response_text = response_text
        self.last_prompt = ""
        self.last_context = None

    async def generate(self, context: AIContext, prompt: str, **kwargs: Any) -> str:
        self.last_prompt = prompt
        self.last_context = context
        tracker = kwargs.get("tracker")
        routing_decision = kwargs.get("routing_decision")
        selected_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else "mock-llama-3-8b")
        if tracker:
            tracker.record_str("provider_name", "mock")
            tracker.record_str("selected_model", selected_model)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)

            config = kwargs.get("config") or kwargs.get("inference_config")
            max_tokens = config.max_tokens if config else kwargs.get("max_tokens", 512)
            tracker.record_count("max_tokens_budget", max_tokens)
            tracker.record_count("effective_max_tokens", max_tokens)

            from app.ai.inference.tokenizer import get_tokenizer
            tokenizer = get_tokenizer()
            p_tok = tokenizer.count_tokens(prompt)
            g_tok = tokenizer.count_tokens(self.response_text)
            tracker.record_count("prompt_tokens", p_tok)
            tracker.record_count("generated_tokens", g_tok)
            tracker.record("generation_ms", 10.0)
            tracker.record("total_llm_ms", 10.0)
            tracker.record("tokens_per_second", 150.0)
            tracker.record_str("request_status", "SUCCESS")
        return self.response_text

    async def generate_stream(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        self.last_prompt = prompt
        self.last_context = context
        routing_decision = kwargs.get("routing_decision")
        selected_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else "mock-llama-3-8b")
        if tracker:
            tracker.record_str("provider_name", "mock")
            tracker.record_str("selected_model", selected_model)
            tracker.record_flag("streaming_used", True)
            tracker.record("ttft_ms", 1.5)
            tracker.record("time_to_first_token_ms", 1.5)
            tracker.record("time_to_first_byte_ms", 1.5)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)

            config = kwargs.get("config") or kwargs.get("inference_config")
            eff_max = config.max_tokens if config else (max_tokens or 512)
            tracker.record_count("max_tokens_budget", eff_max)
            tracker.record_count("effective_max_tokens", eff_max)

            from app.ai.inference.tokenizer import get_tokenizer
            tokenizer = get_tokenizer()
            p_tok = tokenizer.count_tokens(prompt)
            g_tok = tokenizer.count_tokens(self.response_text)
            tracker.record_count("prompt_tokens", p_tok)
            tracker.record_count("generated_tokens", g_tok)
            tracker.record("generation_ms", 12.0)
            tracker.record("total_llm_ms", 13.5)
            tracker.record("tokens_per_second", 120.0)
            tracker.record_str("request_status", "SUCCESS")

        words = self.response_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class MockEmbeddingProvider(EmbeddingProvider):
    """Generates dummy vector floats without external network access."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        # Return a deterministic mock vector matching the requested dimension
        # Use a simple hashing or pattern so different texts produce slightly different vectors
        base = [0.1 * ((i % 10) + 1) for i in range(self.dim)]
        if text:
            mod = (sum(ord(c) for c in text) % 10) * 0.01
            base = [x + mod for x in base]
        return base
