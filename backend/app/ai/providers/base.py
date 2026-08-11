"""
Abstract base classes (interfaces) for LLM and Embedding providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.ai.schemas.advisor import AIContext


class LLMProvider(ABC):
    """Abstraction layer for text generation models (local, API, or cloud-based)."""

    @abstractmethod
    async def generate(self, context: AIContext, prompt: str) -> str:
        """
        Generate text response given the context and formatted prompt.

        Args:
            context: The structured context container (user facts + RAG knowledge).
            prompt: The final system/user prompt string.

        Returns:
            str: Raw LLM response string.

        Raises:
            AIProviderError: When the underlying provider API fails.
            AIConfigurationError: When the provider credentials are missing.
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
