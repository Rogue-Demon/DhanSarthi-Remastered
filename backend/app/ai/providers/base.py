"""
Abstract base classes (interfaces) for LLM and Embedding providers.

Phase L.7.3 additions:
  - aclose(): graceful async shutdown hook for persistent HTTP clients
  - generate() supports optional stream=True via **kwargs for SSE streaming
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from app.ai.schemas.advisor import AIContext


class LLMProvider(ABC):
    """Abstraction layer for text generation models (local, API, or cloud-based)."""

    @abstractmethod
    async def generate(self, context: AIContext, prompt: str, **kwargs: Any) -> str:
        """
        Generate text response given the context and formatted prompt.

        Kwargs:
            tracker: Optional LatencyTracker for observability recording.
            max_tokens: Per-request token budget override.
            stream: bool — if True and provider supports SSE, yield chunks via
                    generate_stream() instead.  Most callers use generate() (non-streaming).

        Returns:
            str: Raw LLM response string (complete, not streamed).

        Raises:
            AIProviderError: When the underlying provider API fails.
            AIConfigurationError: When the provider credentials are missing.
        """
        pass

    async def generate_stream(
        self, context: AIContext, prompt: str, **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        Yield response chunks as an async iterator (SSE streaming path).

        Default implementation falls back to a single-shot generate() call
        wrapped in a one-element iterator.  Override in providers that support
        real SSE streaming.

        Raises:
            AIProviderError: When the underlying provider API fails.
        """
        text = await self.generate(context, prompt, **kwargs)
        yield text

    async def aclose(self) -> None:
        """
        Gracefully close any persistent resources (HTTP clients, connection pools).

        Called by the FastAPI lifespan shutdown hook.  Default is a no-op for
        providers that hold no persistent connections (e.g. MockLLMProvider).
        """
        pass


class EmbeddingProvider(ABC):
    """Abstraction layer for generating semantic vector embeddings."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Generate a list of floats representing the semantic embedding vector.

        Args:
            text: Text block to encode.

        Returns:
            list[float]: Embedding vector.

        Raises:
            AIProviderError: When the embedding model API fails.
        """
        pass

    async def aclose(self) -> None:
        """Gracefully close persistent resources. No-op by default."""
        pass
