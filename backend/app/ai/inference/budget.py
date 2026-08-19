"""
Deterministic Complexity Classifier and Adaptive Token Budget Selector for Phase L.7.4.

Classifies incoming queries into InferenceComplexity tiers (SIMPLE, MODERATE, COMPLEX)
and selects optimal output token budgets and conversation history message limits.
NO LLM calls are made for complexity classification or budget selection.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.router import QueryIntent
from app.core.config import settings

logger = logging.getLogger(__name__)

# Approximate characters-per-token estimate for quick, deterministic token count calculation.
# LLaMA / BPE tokenizers average ~3.8–4.0 chars/token on English/Hinglish financial text.
CHARS_PER_TOKEN_ESTIMATE: float = 4.0


class InferenceComplexityClassifier:
    """Classifies user queries deterministically into SIMPLE, MODERATE, or COMPLEX."""

    def classify(
        self,
        query: str,
        intent: Optional[QueryIntent] = None,
        execution_plan: Optional[Any] = None,
        sub_intent: Optional[Any] = None,
        personalization_level: Optional[str] = None,
        temporal_references: Optional[list] = None,
    ) -> InferenceComplexity:
        """
        Determine query complexity tier based on query structure, intent, and execution plan.
        """
        q_clean = query.strip().lower()

        # 1. CASUAL or simple greetings -> SIMPLE
        if intent == QueryIntent.CASUAL:
            return InferenceComplexity.SIMPLE

        # 2. Check execution plan details
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else None
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else None
        is_comparison = bool(execution_plan and execution_plan.comparison_info and execution_plan.comparison_info.is_comparison)
        is_planning = op_str == "PLANNING" or any(kw in q_clean for kw in ["plan", "strategy", "roadmap", "retire", "prioritize", "priority"])
        is_historical = bool(temporal_references and any(getattr(t, "is_historical", False) for t in temporal_references))

        # 3. COMPLEX Tier conditions:
        #    - Explicit financial planning operation
        #    - Multi-factor debt vs investment tradeoff queries
        #    - Comprehensive multi-domain personal analysis
        if is_planning:
            return InferenceComplexity.COMPLEX

        if any(phrase in q_clean for phrase in ["prioritize", "should i pay", "vs invest", "loan or invest", "retirement plan", "detailed plan"]):
            return InferenceComplexity.COMPLEX

        if personalization_level == "DEEP" and intent == QueryIntent.MIXED:
            return InferenceComplexity.COMPLEX

        # 4. MODERATE Tier conditions:
        #    - Comparisons ("SIP vs FD")
        #    - Personal financial analysis or health assessment
        #    - Historical analysis
        #    - Mixed intent queries
        if is_comparison or is_historical:
            return InferenceComplexity.MODERATE

        if intent in (QueryIntent.PERSONAL_FINANCE, QueryIntent.MIXED) or scope_str in ("PERSONAL_LOOKUP", "PERSONAL_ANALYSIS"):
            return InferenceComplexity.MODERATE

        if any(kw in q_clean for kw in ["how am i", "my status", "health score", "compare", "difference"]):
            return InferenceComplexity.MODERATE

        # 5. SIMPLE Tier default (e.g. "What is SIP?", "Explain 80C")
        if intent == QueryIntent.GENERAL_FINANCE and len(q_clean.split()) < 12:
            return InferenceComplexity.SIMPLE

        return InferenceComplexity.SIMPLE


class AdaptiveTokenBudgetSelector:
    """Selects output token budgets and history message limits adaptively per request."""

    def select_config(
        self,
        query: str,
        intent: Optional[QueryIntent] = None,
        execution_plan: Optional[Any] = None,
        sub_intent: Optional[Any] = None,
        personalization_level: Optional[str] = None,
        temporal_references: Optional[list] = None,
    ) -> InferenceConfig:
        """
        Build a complete request-level InferenceConfig object.
        """
        classifier = InferenceComplexityClassifier()
        complexity = classifier.classify(
            query=query,
            intent=intent,
            execution_plan=execution_plan,
            sub_intent=sub_intent,
            personalization_level=personalization_level,
            temporal_references=temporal_references,
        )

        # Output Token Budget determination
        budget = self._select_token_budget(intent, execution_plan, complexity)

        # History message count limit determination
        history_limit = self._select_history_limit(intent, execution_plan, complexity)

        return InferenceConfig(
            complexity=complexity,
            max_tokens=budget,
            temperature=settings.ai_temperature,
            history_limit=history_limit,
            max_context_chars=settings.ai_max_context_chars,
            max_rag_context_chars=settings.ai_max_rag_context_chars,
            max_personal_context_chars=settings.ai_max_personal_context_chars,
            max_history_chars=settings.ai_max_history_chars,
            estimated_output_tokens=budget,
        )

    def _select_token_budget(
        self,
        intent: Optional[QueryIntent],
        execution_plan: Optional[Any],
        complexity: InferenceComplexity,
    ) -> int:
        """Select output token budget bounded by settings.ai_max_tokens and global safety ceiling."""
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else None
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else None
        is_comparison = bool(execution_plan and execution_plan.comparison_info and execution_plan.comparison_info.is_comparison)

        if intent == QueryIntent.CASUAL:
            raw_budget = getattr(settings, "ai_max_tokens_casual", 128)

        elif complexity == InferenceComplexity.SIMPLE:
            raw_budget = getattr(settings, "ai_simple_max_tokens", 256)

        elif op_str == "PLANNING" or complexity == InferenceComplexity.COMPLEX:
            raw_budget = getattr(settings, "ai_complex_max_tokens", 768)

        elif is_comparison or scope_str == "COMPARISON":
            raw_budget = getattr(settings, "ai_moderate_max_tokens", 512)

        elif intent in (QueryIntent.PERSONAL_FINANCE, QueryIntent.MIXED) or scope_str in ("PERSONAL_LOOKUP", "PERSONAL_ANALYSIS"):
            raw_budget = getattr(settings, "ai_moderate_max_tokens", 512)

        elif complexity == InferenceComplexity.MODERATE:
            raw_budget = getattr(settings, "ai_moderate_max_tokens", 512)

        else:
            raw_budget = getattr(settings, "ai_simple_max_tokens", 256)

        # Enforce global safety max and settings.ai_max_tokens upper bounds
        effective_max = min(raw_budget, settings.ai_max_tokens)
        effective_max = min(effective_max, settings.ai_max_tokens_global_safety_max)
        return effective_max

    def _select_history_limit(
        self,
        intent: Optional[QueryIntent],
        execution_plan: Optional[Any],
        complexity: InferenceComplexity,
    ) -> int:
        """Determine adaptive history message limit."""
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else None
        if intent == QueryIntent.CASUAL:
            adaptive_limit = 2
        elif complexity == InferenceComplexity.SIMPLE:
            adaptive_limit = 4
        elif intent == QueryIntent.PERSONAL_FINANCE or scope_str == "PERSONAL_LOOKUP":
            adaptive_limit = 6
        elif complexity == InferenceComplexity.MODERATE:
            adaptive_limit = 8
        elif complexity == InferenceComplexity.COMPLEX:
            adaptive_limit = 10
        else:
            adaptive_limit = 6

        # Cap at configured global max history messages
        return min(adaptive_limit, settings.ai_max_history_messages)
