"""
Custom exceptions for the DhanSarthi AI Advisor and RAG layer.
"""

from __future__ import annotations

from app.core.exceptions import DhanSarthiError


class AIAdvisorError(DhanSarthiError):
    """Base exception for all AI Advisor errors."""
    pass


class AIProviderError(AIAdvisorError):
    """Raised when the LLM provider fails (timeout, invalid credentials, rate limit, etc.)."""
    pass


class AIConfigurationError(AIAdvisorError):
    """Raised when an AI provider or model is misconfigured or missing credentials."""
    pass


class AISafetyError(AIAdvisorError):
    """Raised when safety checks fail (unsafe keywords, secrets leak, etc.)."""
    pass


class RAGRetrievalError(AIAdvisorError):
    """Raised when the RAG knowledge retriever fails."""
    pass
