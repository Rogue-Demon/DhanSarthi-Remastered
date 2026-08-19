"""
Phase L.7.2 — Token Budget Selector for DhanSarthi AI Advisor.

Maps query intent and scope to a calibrated max_tokens ceiling.
Prevents wasteful over-generation for simple queries (e.g., greetings request
the same token budget as complex financial analysis under the old single-value config).

Rules:
- CASUAL → smallest budget (128 tokens)
- PERSONAL_LOOKUP → moderate (300 tokens)
- SIMPLE GENERAL / DEFINE / EXPLAIN → 256 tokens
- MIXED → 450 tokens
- COMPARISON → 600 tokens
- HISTORICAL / AUTHORITY → 600 tokens
- COMPLEX ANALYSIS (PERSONAL_HEALTH, full MIXED) → 800 tokens
- Global safety max: never exceed ai_max_tokens_global_safety_max (1024)

All budget values are configurable via Settings env vars.
Never log query content, credentials, or financial numbers.
"""

from __future__ import annotations

from typing import Optional

from app.ai.router import QueryIntent
from app.core.config import settings


class TokenBudgetSelector:
    """
    Deterministic, settings-driven max_tokens budget selector.

    Usage:
        budget = TokenBudgetSelector().select(intent, scope, operation)
        response = await llm.generate(..., max_tokens=budget)
    """

    def select(
        self,
        intent: QueryIntent,
        scope: Optional[str] = None,
        operation: Optional[str] = None,
        is_comparison: bool = False,
        is_historical: bool = False,
        is_authority_sensitive: bool = False,
    ) -> int:
        """
        Select a safe max_tokens budget for the given query classification.

        Args:
            intent: Classified QueryIntent from Phase L.1/L.2.
            scope: QueryScope string value (e.g., 'EDUCATIONAL', 'PERSONAL_LOOKUP', etc.)
            operation: OperationType string value (e.g., 'DEFINE', 'EXPLAIN', 'COMPARE', etc.)
            is_comparison: True if query is a comparison query.
            is_historical: True if query contains historical temporal references.
            is_authority_sensitive: True if query references RBI, SEBI, tax authority, etc.

        Returns:
            int: max_tokens budget, always <= ai_max_tokens_global_safety_max.
        """
        safety_max = settings.ai_max_tokens_global_safety_max

        # 1. CASUAL — absolute minimum budget
        if intent == QueryIntent.CASUAL:
            return min(settings.ai_max_tokens_casual, safety_max)

        # 2. PERSONAL_FINANCE / PERSONAL_LOOKUP — local engine handles numbers,
        #    LLM only needs to format and explain
        if intent == QueryIntent.PERSONAL_FINANCE:
            scope_upper = (scope or "").upper()
            if scope_upper in ("PERSONAL_LOOKUP", ""):
                return min(settings.ai_max_tokens_personal_lookup, safety_max)
            # Personal health / full analysis — needs more room
            return min(settings.ai_max_tokens_analysis, safety_max)

        # 3. COMPARISON — expanded context, needs more tokens
        if is_comparison or (operation or "").upper() == "COMPARE":
            return min(settings.ai_max_tokens_comparison, safety_max)

        # 4. HISTORICAL / AUTHORITY — research-heavy, similar budget to comparison
        if is_historical or is_authority_sensitive:
            return min(settings.ai_max_tokens_historical, safety_max)

        # 5. GENERAL FINANCE — depends on operation type
        if intent == QueryIntent.GENERAL_FINANCE:
            op_upper = (operation or "").upper()
            if op_upper in ("DEFINE", "EXPLAIN"):
                return min(settings.ai_max_tokens_simple_general, safety_max)
            # Other general queries (ANALYZE, RECOMMEND, etc.)
            return min(settings.ai_max_tokens_analysis, safety_max)

        # 6. MIXED — personal metrics + general guidance
        if intent == QueryIntent.MIXED:
            return min(settings.ai_max_tokens_mixed, safety_max)

        # 7. Default fallback: use legacy global max_tokens setting
        return min(settings.ai_max_tokens, safety_max)
