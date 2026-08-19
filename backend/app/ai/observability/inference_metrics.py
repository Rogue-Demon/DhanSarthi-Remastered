"""
Real Inference Profiling & Metrics Calculator for DhanSarthi Phase L.8.

Provides timing helpers and token throughput calculators for both streaming
and non-streaming Hugging Face LLM provider calls.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


class RealInferenceMetricsTracker:
    """Helper container for timing real LLM provider requests."""

    def __init__(self, model_name: str, provider_name: str, is_streaming: bool = False) -> None:
        self.model_name = model_name
        self.provider_name = provider_name
        self.is_streaming = is_streaming

        self.request_start_time: Optional[float] = None
        self.first_token_time: Optional[float] = None
        self.request_end_time: Optional[float] = None

        self.prompt_tokens: int = 0
        self.generated_tokens: int = 0

    def start_request(self) -> None:
        self.request_start_time = time.perf_counter()

    def record_first_token(self) -> float:
        """Record TTFT (Time To First Token) for streaming requests."""
        now = time.perf_counter()
        if self.first_token_time is None:
            self.first_token_time = now
        if self.request_start_time is not None:
            return (now - self.request_start_time) * 1000.0
        return 0.0

    def finish_request(self, prompt_tokens: int = 0, generated_tokens: int = 0) -> Dict[str, Any]:
        self.request_end_time = time.perf_counter()
        self.prompt_tokens = prompt_tokens
        self.generated_tokens = generated_tokens

        start = self.request_start_time or self.request_end_time
        end = self.request_end_time

        total_provider_ms = (end - start) * 1000.0 if start and end else 0.0

        if self.is_streaming and self.first_token_time:
            ttft_ms = (self.first_token_time - start) * 1000.0 if start else 0.0
            generation_ms = (end - self.first_token_time) * 1000.0
            provider_network_ms = ttft_ms
        else:
            ttft_ms = None
            generation_ms = total_provider_ms
            provider_network_ms = 0.0

        # Calculate tokens per second (generation throughput)
        gen_seconds = (generation_ms / 1000.0) if generation_ms > 0 else 0.001
        tokens_per_second = round(generated_tokens / gen_seconds, 2) if generated_tokens > 0 else 0.0

        return {
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "is_streaming": self.is_streaming,
            "total_provider_ms": round(total_provider_ms, 2),
            "ttft_ms": round(ttft_ms, 2) if ttft_ms is not None else None,
            "generation_ms": round(generation_ms, 2),
            "provider_network_ms": round(provider_network_ms, 2),
            "prompt_tokens": prompt_tokens,
            "generated_tokens": generated_tokens,
            "tokens_per_second": tokens_per_second,
        }
