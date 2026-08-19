"""
Inference configuration schemas and complexity classifications for Phase L.7.4.

Defines:
  - InferenceComplexity: Enum representing query complexity tiers (SIMPLE, MODERATE, COMPLEX).
  - InferenceConfig: Request-level dataclass/pydantic model holding adaptive token budgets,
    context character limits, history limits, and token estimates.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InferenceComplexity(str, Enum):
    """Complexity classification tier for LLM inference workload management."""
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"


class InferenceConfig(BaseModel):
    """
    Request-level configuration created once per request.
    Passed through both standard generate() and generate_stream() calls.
    """
    complexity: InferenceComplexity = Field(
        default=InferenceComplexity.MODERATE,
        description="Query complexity level (SIMPLE, MODERATE, COMPLEX)"
    )
    max_tokens: int = Field(
        default=512,
        description="Effective output token limit passed to the LLM provider"
    )
    temperature: float = Field(
        default=0.2,
        description="LLM generation temperature"
    )
    history_limit: int = Field(
        default=6,
        description="Maximum number of history messages to include"
    )
    max_context_chars: int = Field(
        default=12000,
        description="Maximum total assembled prompt character length"
    )
    max_rag_context_chars: int = Field(
        default=7000,
        description="Maximum total RAG knowledge context character length"
    )
    max_personal_context_chars: int = Field(
        default=4000,
        description="Maximum total personal financial context character length"
    )
    max_history_chars: int = Field(
        default=5000,
        description="Maximum conversation history character length"
    )

    # Token Estimates
    estimated_prompt_tokens: int = Field(
        default=0,
        description="Approximate input prompt token count"
    )
    estimated_output_tokens: int = Field(
        default=0,
        description="Approximate expected response token count"
    )
    estimated_total_tokens: int = Field(
        default=0,
        description="Approximate total token workload (prompt + response)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a dictionary for logging/observability."""
        return self.model_dump()
