"""
Phase L.9.6 — Cache Eligibility Policy for DhanSarthi AI Advisor.

Determines deterministically whether an incoming query and its context
are eligible for response caching.

CRITICAL SAFETY INVARIANT:
Personal financial data, user holdings, market-sensitive data, or
user calculations must NEVER be cached or served from a shared cache.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.ai.router import QueryIntent, SubIntent
from app.core.config import settings


PERSONAL_PRONOUNS_PATTERN = re.compile(
    r"\b(my|mine|i|me|we|us|our|ours|myself)\b", re.IGNORECASE
)

PERSONAL_FINANCE_KEYWORDS = re.compile(
    r"\b(salary|expense|expenses|spending|spent|budget|debt|loan|emi|net worth|"
    r"portfolio|holding|holdings|asset|assets|liability|liabilities|saving|savings|"
    r"account|balance|transaction|transactions|afford|invested)\b",
    re.IGNORECASE,
)

LIVE_MARKET_KEYWORDS = re.compile(
    r"\b(live|today|current|now|price|prices|nav|rate|rates|sensex|nifty|"
    r"market today|stock price|gold price today|crypto|ticker)\b",
    re.IGNORECASE,
)


class CacheEligibilityPolicy:
    """
    Evaluates query metadata and context to enforce strict cache eligibility.
    """

    ELIGIBLE_SCOPES = frozenset({
        "EDUCATIONAL",
        "DEFINITION",
        "EXPLAIN",
        "OVERVIEW",
        "GENERAL",
        "",
    })

    ELIGIBLE_OPERATIONS = frozenset({
        "DEFINE",
        "EXPLAIN",
        "OVERVIEW",
        "LIST",
        "",
    })

    INELIGIBLE_INTENTS = frozenset({
        QueryIntent.PERSONAL_FINANCE,
        QueryIntent.MIXED,
        QueryIntent.CASUAL,
    })

    INELIGIBLE_SUB_INTENTS = frozenset({
        SubIntent.PERSONAL_HEALTH,
        SubIntent.SPENDING_ANALYSIS,
        SubIntent.DEBT_ANALYSIS,
        SubIntent.INVESTMENT_ANALYSIS,
        SubIntent.GOAL_ANALYSIS,
        SubIntent.NET_WORTH_ANALYSIS,
        SubIntent.FINANCIAL_PLANNING,
    })

    @classmethod
    def is_cache_enabled(cls) -> bool:
        """Check if response caching is enabled in settings."""
        return bool(
            settings.ai_response_cache_enabled
            and settings.ai_cache_educational_enabled
        )

    @classmethod
    def is_eligible(
        cls,
        query: str,
        intent: QueryIntent,
        scope: Optional[str] = None,
        operation: Optional[str] = None,
        has_personal_context: bool = False,
        has_live_market_data: bool = False,
        requires_financial_engine: bool = False,
        requires_market_data: bool = False,
        is_ambiguous: bool = False,
        is_adversarial: bool = False,
    ) -> bool:
        """
        Determine whether a query is strictly eligible for response caching.

        Returns True ONLY if all safety and educational criteria are satisfied.
        Fail closed: any ambiguity or risk returns False.
        """
        # 1. Global toggle check
        if not cls.is_cache_enabled():
            return False

        # 2. Safety / Adversarial / Ambiguity check
        if is_adversarial or is_ambiguous:
            return False

        # 3. Personal context boundary (NON-NEGOTIABLE)
        if has_personal_context:
            return False

        # 4. Market data boundary
        if has_live_market_data or requires_market_data:
            return False

        # 5. Financial engine requirement
        if requires_financial_engine:
            return False

        # 6. Intent check: MUST be GENERAL_FINANCE
        if intent != QueryIntent.GENERAL_FINANCE or intent in cls.INELIGIBLE_INTENTS:
            return False

        # 7. Scope check: MUST be educational/general
        if scope is not None:
            scope_clean = str(scope).strip().upper()
            if scope_clean not in cls.ELIGIBLE_SCOPES:
                return False

        # 8. Operation check
        if operation is not None:
            op_clean = str(operation).strip().upper()
            if op_clean not in cls.ELIGIBLE_OPERATIONS:
                return False

        # 9. Query text deep scan for personal pronouns or live market markers
        if not query or not query.strip():
            return False

        q_clean = query.strip()
        if PERSONAL_PRONOUNS_PATTERN.search(q_clean) and PERSONAL_FINANCE_KEYWORDS.search(q_clean):
            # Example: "How much is my salary?", "What is my net worth?"
            return False

        if LIVE_MARKET_KEYWORDS.search(q_clean) and ("today" in q_clean.lower() or "now" in q_clean.lower() or "price" in q_clean.lower()):
            # Example: "What is the live gold price today?", "Current Nifty NAV"
            return False

        return True
