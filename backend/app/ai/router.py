"""
Intent Router for DhanSarthi AI Advisor.

Provides lightweight, deterministic query intent classification before RAG retrieval.
Categorizes user queries into:
  - CASUAL: Greetings, acknowledgements, capabilities queries.
  - GENERAL_FINANCE: Educational questions about concepts, rules, terms.
  - PERSONAL_FINANCE: Queries strictly about user's own financial metrics/data.
  - MIXED: Guidance queries combining user's metrics with general financial principles.
"""

from __future__ import annotations

import enum
import re
from typing import Dict, Any


class QueryIntent(str, enum.Enum):
    """Categorization of incoming user queries."""

    CASUAL = "CASUAL"
    GENERAL_FINANCE = "GENERAL_FINANCE"
    PERSONAL_FINANCE = "PERSONAL_FINANCE"
    MIXED = "MIXED"


class SubIntent(str, enum.Enum):
    """Sub-intent classification for personalized financial reasoning."""

    PERSONAL_HEALTH = "PERSONAL_HEALTH"
    SPENDING_ANALYSIS = "SPENDING_ANALYSIS"
    DEBT_ANALYSIS = "DEBT_ANALYSIS"
    INVESTMENT_ANALYSIS = "INVESTMENT_ANALYSIS"
    GOAL_ANALYSIS = "GOAL_ANALYSIS"
    NET_WORTH_ANALYSIS = "NET_WORTH_ANALYSIS"
    FINANCIAL_PLANNING = "FINANCIAL_PLANNING"
    GENERAL = "GENERAL"


class IntentRouter:
    """Lightweight deterministic query intent router."""

    # Casual greeting / meta phrases
    CASUAL_PATTERNS = [
        r"^(hi|hello|hey|greetings|hola|namaste|good morning|good afternoon|good evening)(\s+dhansarthi|\s+bot|\s+there)?[\s!.]*$",
        r"^(how are you|how\'s it going|what\'s up|sup)(\s+dhansarthi|\s+bot|\s+there)?[\s!?.]*$",
        r"^(thanks|thank you|thanks a lot|thx)(\s+dhansarthi|\s+bot|\s+there)?[\s!.]*$",
        r"^(what can you do|what are your capabilities|who are you|how can you help me|tell me about yourself)[\s!?.]*$",
    ]

    # Explicit user data indicators
    PERSONAL_FACT_INDICATORS = [
        r"\bmy\b",
        r"\bme\b",
        r"\bi\b",
        r"\bdid i\b",
        r"\bcan i\b",
        r"\bdo i have\b",
        r"\bmy spending\b",
        r"\bmy expenses?\b",
        r"\bmy income\b",
        r"\bmy net worth\b",
        r"\bmy debt\b",
        r"\bmy loans?\b",
        r"\bmy portfolio\b",
        r"\bmy budget\b",
        r"\bmy savings?\b",
    ]

    # Advice / evaluation / recommendation indicators (indicates MIXED if personal facts also present)
    ADVICE_INDICATORS = [
        r"\bshould i\b",
        r"\bwhat should i do\b",
        r"\bis my \w+ (good|healthy|bad|high|low|okay)\b",
        r"\bhow to improve\b",
        r"\bhow can i improve\b",
        r"\bhow to reduce\b",
        r"\bhow to increase\b",
        r"\bbased on my\b",
        r"\brecommend\b",
        r"\badvice\b",
        r"\bstrategy\b",
        r"\bplan for me\b",
    ]

    # Educational / general knowledge indicators
    GENERAL_KNOWLEDGE_INDICATORS = [
        r"\bwhat is\b",
        r"\bwhat are\b",
        r"\bdefine\b",
        r"\bexplain\b",
        r"\bhow does \w+ work\b",
        r"\bmeaning of\b",
        r"\bdifference between\b",
        r"\btypes of\b",
        r"\bbenefits of\b",
        r"\badvantages of\b",
    ]

    def classify(self, query: str) -> QueryIntent:
        """
        Classify the query into one of QueryIntent enum values.

        Args:
            query: Raw user message string.

        Returns:
            QueryIntent: The classified intent.
        """
        if not query or not query.strip():
            return QueryIntent.CASUAL

        q_clean = query.strip().lower()

        # 1. Check for casual matches
        for pattern in self.CASUAL_PATTERNS:
            if re.search(pattern, q_clean):
                return QueryIntent.CASUAL

        # Also casual short phrases like "hi dhan sarthi", "hello there"
        if q_clean in {"hi", "hello", "hey", "good morning", "good afternoon", "thanks", "thank you"}:
            return QueryIntent.CASUAL

        # 2. Check for personal indicators and advice indicators
        has_personal = any(re.search(pat, q_clean) for pat in self.PERSONAL_FACT_INDICATORS)
        has_advice = any(re.search(pat, q_clean) for pat in self.ADVICE_INDICATORS)
        has_general_q = any(re.search(pat, q_clean) for pat in self.GENERAL_KNOWLEDGE_INDICATORS)

        # 3. Mixed Intent decision: references personal data AND seeks advice / comparison / general concept strategy
        if has_personal and (has_advice or ("sip" in q_clean or "debt" in q_clean or "savings rate" in q_clean or "budget" in q_clean)):
            # Special check: pure personal data extraction vs mixed advice query
            # e.g., "How much did I spend this month?" -> PERSONAL_FINANCE
            # "Is my spending high?" or "What should I do about my debt?" -> MIXED
            if has_advice or any(kw in q_clean for kw in ["healthy", "good", "high", "increasing", "what should", "should i"]):
                return QueryIntent.MIXED

        # 4. Pure Personal Finance query decision
        if has_personal:
            # e.g., "How much did I spend this month?", "What is my net worth?", "How much debt do I have?"
            return QueryIntent.PERSONAL_FINANCE

        # 5. Otherwise, default to General Finance for financial questions or Mixed fallback
        return QueryIntent.GENERAL_FINANCE

    def classify_sub_intent(self, query: str) -> SubIntent:
        """
        Classify personalized queries into granular sub-intents.
        """
        if not query or not query.strip():
            return SubIntent.GENERAL

        q_clean = query.strip().lower()

        if any(kw in q_clean for kw in ["health", "doing financially", "how am i doing", "health check", "financial position"]):
            return SubIntent.PERSONAL_HEALTH
        if any(kw in q_clean for kw in ["spend", "spending", "expense", "overspending", "category"]):
            return SubIntent.SPENDING_ANALYSIS
        if any(kw in q_clean for kw in ["debt", "loan", "emi", "payoff", "prioritize my debt"]):
            return SubIntent.DEBT_ANALYSIS
        if any(kw in q_clean for kw in ["invest", "portfolio", "sip", "risk", "diversified", "stocks", "mutual fund"]):
            return SubIntent.INVESTMENT_ANALYSIS
        if any(kw in q_clean for kw in ["goal", "afford", "target date", "buy a house"]):
            return SubIntent.GOAL_ANALYSIS
        if any(kw in q_clean for kw in ["net worth", "assets", "liabilities", "wealth"]):
            return SubIntent.NET_WORTH_ANALYSIS
        if any(kw in q_clean for kw in ["emergency fund", "prioritize", "runway", "saving enough", "savings rate"]):
            return SubIntent.FINANCIAL_PLANNING

        return SubIntent.GENERAL

    def get_required_data_fields(
        self, intent: QueryIntent, sub_intent: Optional[SubIntent] = None
    ) -> Dict[str, bool]:
        """
        Map query intent & sub-intent to exact required user financial data fields.
        """
        if intent == QueryIntent.CASUAL:
            return {
                "needs_cash_flow": False,
                "needs_net_worth": False,
                "needs_investments": False,
                "needs_loans": False,
                "needs_goals": False,
                "needs_budgets": False,
            }

        # Default for PERSONAL_HEALTH or GENERAL PERSONAL/MIXED: load full context
        if sub_intent == SubIntent.PERSONAL_HEALTH or intent == QueryIntent.MIXED:
            return {
                "needs_cash_flow": True,
                "needs_net_worth": True,
                "needs_investments": True,
                "needs_loans": True,
                "needs_goals": True,
                "needs_budgets": True,
            }

        if sub_intent == SubIntent.SPENDING_ANALYSIS:
            return {
                "needs_cash_flow": True,
                "needs_net_worth": False,
                "needs_investments": False,
                "needs_loans": False,
                "needs_goals": False,
                "needs_budgets": True,
            }

        if sub_intent == SubIntent.DEBT_ANALYSIS:
            return {
                "needs_cash_flow": True,
                "needs_net_worth": True,
                "needs_investments": True,
                "needs_loans": True,
                "needs_goals": False,
                "needs_budgets": False,
            }

        if sub_intent == SubIntent.INVESTMENT_ANALYSIS:
            return {
                "needs_cash_flow": True,
                "needs_net_worth": True,
                "needs_investments": True,
                "needs_loans": False,
                "needs_goals": False,
                "needs_budgets": False,
            }

        if sub_intent == SubIntent.GOAL_ANALYSIS:
            return {
                "needs_cash_flow": True,
                "needs_net_worth": True,
                "needs_investments": False,
                "needs_loans": False,
                "needs_goals": True,
                "needs_budgets": False,
            }

        if sub_intent == SubIntent.NET_WORTH_ANALYSIS:
            return {
                "needs_cash_flow": False,
                "needs_net_worth": True,
                "needs_investments": True,
                "needs_loans": True,
                "needs_goals": False,
                "needs_budgets": False,
            }

        return {
            "needs_cash_flow": True,
            "needs_net_worth": True,
            "needs_investments": True,
            "needs_loans": True,
            "needs_goals": True,
            "needs_budgets": True,
        }
