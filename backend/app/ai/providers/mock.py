"""
Mock model providers for unit testing and offline development.
"""

from __future__ import annotations

from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.schemas.advisor import AIContext


class MockLLMProvider(LLMProvider):
    """Generates deterministic mock responses without external network access."""

    def __init__(self, response_text: str = "Mock financial guidance response.") -> None:
        self.response_text = response_text
        self.last_prompt = ""
        self.last_context = None

    async def generate(self, context: AIContext, prompt: str) -> str:
        self.last_prompt = prompt
        self.last_context = context
        return self.response_text


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
