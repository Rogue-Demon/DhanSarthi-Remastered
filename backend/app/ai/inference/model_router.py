"""
Adaptive Model Selection Router for DhanSarthi Phase L.8.

Determines active LLM model candidates per request based on query complexity,
intent, and trusted server allowlist constraints.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Set

from pydantic import BaseModel, Field

from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.router import QueryIntent
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRoutingDecision(BaseModel):
    """Container for model selection decisions per request."""

    model: str = Field(description="Active Hugging Face model identifier selected for this request")
    reason: str = Field(description="Deterministic rationale for model choice")
    complexity: InferenceComplexity = Field(description="Query complexity level")
    expected_latency_class: str = Field(default="BALANCED", description="Latency tier: FAST | BALANCED | REASONING")
    max_tokens: int = Field(default=512, description="Token output budget")
    temperature: float = Field(default=0.2, description="Sampling temperature")


class ModelRouter:
    """Adaptive model router with server allowlist enforcement."""

    def __init__(self) -> None:
        self.enabled = settings.ai_model_routing_enabled
        self.primary_model = settings.ai_model
        self.fast_model = getattr(settings, "ai_fast_model", settings.ai_model)
        self.balanced_model = getattr(settings, "ai_balanced_model", settings.ai_model)
        self.reasoning_model = getattr(settings, "ai_reasoning_model", settings.ai_model)

        raw_allowed = getattr(settings, "ai_allowed_models", settings.ai_model)
        self.allowed_models: Set[str] = {m.strip() for m in raw_allowed.split(",") if m.strip()}
        self.allowed_models.add(self.primary_model)

    def route(
        self,
        query: str,
        intent: Optional[QueryIntent] = None,
        config: Optional[InferenceConfig] = None,
        execution_plan: Optional[Any] = None,
    ) -> ModelRoutingDecision:
        """
        Select an appropriate model candidate for this request.

        Guarantees:
          - If AI_MODEL_ROUTING_ENABLED=false, unconditionally returns settings.ai_model.
          - Never returns a model outside the trusted server allowlist (AI_ALLOWED_MODELS).
          - Does not alter RAG, Financial Engine, or Safety Validator contracts.
        """
        complexity = config.complexity if config else InferenceComplexity.MODERATE
        max_tokens = config.max_tokens if config else settings.ai_max_tokens
        temperature = config.temperature if config else settings.ai_temperature

        # 1. Disabled mode check (default = false for zero-behavior-change guarantee)
        if not self.enabled:
            return ModelRoutingDecision(
                model=self._validate_model(self.primary_model),
                reason="ROUTING_DISABLED",
                complexity=complexity,
                expected_latency_class="BALANCED",
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # 2. Complexity & Intent-based candidate selection
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else None

        if intent == QueryIntent.CASUAL or complexity == InferenceComplexity.SIMPLE:
            candidate = self.fast_model
            latency_class = "FAST"
            reason = f"SIMPLE_QUERY_FAST_ROUTING ({complexity.value})"

        elif op_str == "PLANNING" or complexity == InferenceComplexity.COMPLEX:
            candidate = self.reasoning_model
            latency_class = "REASONING"
            reason = f"COMPLEX_REASONING_ROUTING ({complexity.value})"

        else:
            candidate = self.balanced_model
            latency_class = "BALANCED"
            reason = f"MODERATE_QUERY_BALANCED_ROUTING ({complexity.value})"

        # 3. Validate candidate model against trusted server allowlist
        selected_model = self._validate_model(candidate)

        return ModelRoutingDecision(
            model=selected_model,
            reason=reason,
            complexity=complexity,
            expected_latency_class=latency_class,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _validate_model(self, candidate_model: str) -> str:
        """Ensure candidate model is present in server-configured allowlist."""
        if candidate_model in self.allowed_models:
            return candidate_model

        logger.warning(
            f"Candidate model '{candidate_model}' is not in trusted allowlist ({self.allowed_models}). "
            f"Falling back to primary model '{self.primary_model}'."
        )
        return self.primary_model
