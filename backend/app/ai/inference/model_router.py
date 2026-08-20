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
          - Preserves quality gates: complex planning, tax, and comparisons require BALANCED or REASONING.
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

        # 2. Extract structured signals from execution plan
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else None
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else None
        is_comparison = bool(execution_plan and execution_plan.comparison_info and execution_plan.comparison_info.is_comparison)
        
        # Check if query is tax / regulatory
        is_tax_regulatory = False
        if execution_plan and getattr(execution_plan, "entities", None):
            is_tax_regulatory = any(
                getattr(e, "entity_type", None) and getattr(e.entity_type, "value", "") == "tax_category"
                for e in execution_plan.entities
            )
        if "80C" in query.upper() or "TAX" in query.upper() or "SECTION" in query.upper():
            is_tax_regulatory = True

        # 3. Workload-based deterministic routing logic
        # 3a. Complex Planning & Multi-step Financial Analysis -> REASONING tier
        if op_str in ("PLAN", "PLANNING", "RECOMMEND", "PREDICT") or complexity == InferenceComplexity.COMPLEX or scope_str == "PLANNING":
            candidate = self.reasoning_model
            latency_class = "REASONING"
            reason = f"COMPLEX_PLANNING_ROUTING ({op_str or complexity.value})"

        # 3b. Comparison, Tax/Regulatory, Historical, or Moderate queries -> BALANCED tier minimum
        elif is_comparison or op_str == "COMPARE" or scope_str == "COMPARISON":
            candidate = self.balanced_model
            latency_class = "BALANCED"
            reason = "COMPARISON_QUERY_BALANCED_ROUTING"

        elif is_tax_regulatory:
            candidate = self.balanced_model
            latency_class = "BALANCED"
            reason = "TAX_REGULATORY_BALANCED_ROUTING"

        # 3c. Casual greetings and metadata -> FAST tier
        elif intent == QueryIntent.CASUAL or scope_str == "CASUAL":
            candidate = self.fast_model
            latency_class = "FAST"
            reason = "CASUAL_QUERY_FAST_ROUTING"

        # 3d. Direct Personal Lookups -> FAST tier
        elif (
            intent == QueryIntent.PERSONAL_FINANCE
            and scope_str == "PERSONAL_LOOKUP"
            and op_str in ("LOOKUP", "CHECK", "TRACK", "SUMMARIZE", "EXPLAIN")
            and not is_comparison
        ):
            candidate = self.fast_model
            latency_class = "FAST"
            reason = f"PERSONAL_LOOKUP_FAST_ROUTING ({op_str})"

        # 3e. Simple General Queries -> FAST tier
        elif complexity == InferenceComplexity.SIMPLE and not is_comparison and not is_tax_regulatory:
            candidate = self.fast_model
            latency_class = "FAST"
            reason = f"SIMPLE_QUERY_FAST_ROUTING ({complexity.value})"

        # 3f. Default fallback -> BALANCED tier
        else:
            candidate = self.balanced_model
            latency_class = "BALANCED"
            reason = f"DEFAULT_BALANCED_ROUTING ({complexity.value})"

        # 4. Validate candidate model against trusted server allowlist
        selected_model = self._validate_model(candidate)

        return ModelRoutingDecision(
            model=selected_model,
            reason=reason,
            complexity=complexity,
            expected_latency_class=latency_class,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def get_fallback_model(self, current_model: str, failed_models: Optional[Set[str]] = None) -> Optional[str]:
        """
        Determine the next model candidate in the resilience hierarchy:
        FAST -> BALANCED -> REASONING -> None (Safe Fallback).
        """
        failed = failed_models or set()
        failed.add(current_model)

        tier_order = [self.fast_model, self.balanced_model, self.reasoning_model, self.primary_model]
        for candidate in tier_order:
            if candidate not in failed and candidate in self.allowed_models:
                return candidate
        return None

    def _validate_model(self, candidate_model: str) -> str:
        """Ensure candidate model is present in server-configured allowlist."""
        if candidate_model in self.allowed_models:
            return candidate_model

        logger.warning(
            f"Candidate model '{candidate_model}' is not in trusted allowlist ({self.allowed_models}). "
            f"Falling back to primary model '{self.primary_model}'."
        )
        return self.primary_model
