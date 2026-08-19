"""
Intent, Entity Role & Scope Classifier for DhanSarthi Phase L.2.

Provides 100% deterministic, local, millisecond-level classification of:
  - Query Scope (EDUCATIONAL, PERSONAL_LOOKUP, PERSONAL_ANALYSIS, COMPARISON, PLANNING, MARKET_INFORMATION, TRANSACTIONAL, CASUAL, AMBIGUOUS, MIXED)
  - Operation Type (EXPLAIN, DEFINE, CALCULATE, LOOKUP, ANALYZE, COMPARE, RECOMMEND, PLAN, CHECK, TRACK, ACTION_REQUEST, etc.)
  - Entity Roles (SUBJECT, FILTER, INVESTMENT_TARGET, COMPARISON_LEFT, COMPARISON_RIGHT, PERSONAL_INVESTMENT)
  - Comparison Details & Dimensions
  - Personalization Level (NONE, LOW, MEDIUM, HIGH)
  - Clarification Needs & Prompts
  - Deterministic Backend Data Source Selection (RAG, Financial Engine, Market Data, Conversation Context, User Profile)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    ComparisonInfo,
    EntityRole,
    OperationType,
    PersonalizationLevel,
    QueryExecutionPlan,
    QueryScope,
)
from app.ai.schemas.query_understanding import ExtractedEntity


class IntentScopeClassifier:
    """Deterministic Intent, Entity Role, Scope & Source Selection Classifier."""

    TRANSACTIONAL_KEYWORDS = [
        "buy this stock",
        "buy stock",
        "sell stock",
        "execute trade",
        "transfer money",
        "pay bill",
        "book profit",
        "withdraw money",
        "sell my mutual fund",
    ]

    MARKET_KEYWORDS = [
        "nifty",
        "sensex",
        "gold price",
        "current gold price",
        "stock price",
        "exchange rate",
        "usd/inr",
        "repo rate",
        "market today",
    ]

    AMBIGUOUS_SHORT_QUERIES = {
        "what is it?",
        "what is it",
        "is it safe?",
        "is it safe",
        "should i invest?",
        "should i invest",
        "how much?",
        "how much",
        "is it good?",
        "is it good",
    }

    def build_execution_plan(
        self,
        query: str,
        resolved_query: str,
        intent: QueryIntent,
        sub_intent: SubIntent,
        entities: List[ExtractedEntity],
        conv_reference: Optional[any] = None,
        history: Optional[List] = None,
    ) -> QueryExecutionPlan:
        """
        Build a deterministic QueryExecutionPlan for the given query.

        Execution is millisecond-level, local, and 100% deterministic without LLM calls.
        """
        q_clean = query.strip()
        q_lower = resolved_query.lower() if resolved_query else q_clean.lower()

        # 1. Comparison Detection
        comparison_info = self.detect_comparison(q_lower, entities)

        # 2. Clarification Detection
        clarification_required, clarification_reason, clarification_prompt = self.detect_clarification(
            query=q_clean,
            resolved_query=resolved_query,
            conv_reference=conv_reference,
            entities=entities,
            history=history,
        )

        # 3. Operation Detection
        operation = self.detect_operation(q_lower, intent, comparison_info)

        # 4. Scope Classification
        scope = self.classify_scope(
            q_clean=q_clean,
            q_lower=q_lower,
            intent=intent,
            sub_intent=sub_intent,
            operation=operation,
            comparison_info=comparison_info,
            clarification_required=clarification_required,
        )

        # 5. Entity Roles Assignment
        entity_roles = self.assign_entity_roles(q_lower, entities, comparison_info, intent, scope)

        # 6. Personalization Level
        personalization_level = self.detect_personalization_level(q_lower, intent, scope, entities)

        # 7. Deterministic Source Selection
        (
            requires_rag,
            requires_financial_engine,
            requires_market_data,
            requires_conversation_context,
            requires_user_profile,
            requires_document_context,
        ) = self.determine_data_sources(
            scope=scope,
            intent=intent,
            q_lower=q_lower,
            personalization_level=personalization_level,
            clarification_required=clarification_required,
            history=history,
        )

        return QueryExecutionPlan(
            original_query=q_clean,
            intent=intent,
            sub_intent=sub_intent,
            scope=scope,
            operation=operation,
            entities=entities,
            entity_roles=entity_roles,
            comparison_info=comparison_info,
            personalization_level=personalization_level,
            requires_rag=requires_rag,
            requires_financial_engine=requires_financial_engine,
            requires_market_data=requires_market_data,
            requires_conversation_context=requires_conversation_context,
            requires_user_profile=requires_user_profile,
            requires_document_context=requires_document_context,
            clarification_required=clarification_required,
            clarification_reason=clarification_reason,
            clarification_prompt=clarification_prompt,
            confidence=1.0 if not clarification_required else 0.5,
        )

    def detect_comparison(
        self, q_lower: str, entities: List[ExtractedEntity]
    ) -> ComparisonInfo:
        """Detect comparative queries and extract comparison items & dimensions."""
        # Match explicit comparison keywords
        comp_match = re.search(
            r"\b([\w\s]+?)\s+(?:vs\.?|versus|or|compared\s+to|better\s+than)\s+([\w\s]+?)\b",
            q_lower,
            re.IGNORECASE,
        )

        is_comp = False
        items: List[str] = []
        dimension = "general"
        personal_req = any(w in q_lower for w in ["my", "for me", "i", "mine", "should i"])

        if comp_match:
            item1 = comp_match.group(1).strip()
            item2 = comp_match.group(2).strip()
            # Clean filler words
            item1_clean = re.sub(r"^(is|should i|which is better|choose|between)\s+", "", item1, flags=re.I).strip()
            item2_clean = re.sub(r"\?$", "", item2).strip()

            if item1_clean and item2_clean:
                is_comp = True
                items = [item1_clean.upper() if len(item1_clean) <= 4 else item1_clean.title(),
                         item2_clean.upper() if len(item2_clean) <= 4 else item2_clean.title()]

        if not is_comp and len(entities) >= 2:
            # Check if query asks to compare extracted entities
            if any(w in q_lower for w in ["compare", "difference", "vs", "versus", "or", "better"]):
                is_comp = True
                items = [e.value for e in entities[:2]]

        # Determine dimension
        if "tax" in q_lower or "80c" in q_lower:
            dimension = "tax"
        elif "safe" in q_lower or "risk" in q_lower:
            dimension = "safety"
        elif "return" in q_lower or "yield" in q_lower:
            dimension = "returns"
        elif personal_req or "repay" in q_lower or "invest" in q_lower:
            dimension = "financial_decision"

        return ComparisonInfo(
            is_comparison=is_comp,
            comparison_items=items,
            comparison_dimension=dimension,
            personalization_required=personal_req,
        )

    def detect_clarification(
        self,
        query: str,
        resolved_query: str,
        conv_reference: Optional[any],
        entities: List[ExtractedEntity],
        history: Optional[List],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detect ambiguous queries requiring clarification from user."""
        q_lower = query.strip().lower()

        # Check explicit ambiguous short queries without context
        if q_lower in self.AMBIGUOUS_SHORT_QUERIES:
            if not history or (conv_reference and conv_reference.confidence < 0.5):
                if q_lower in {"should i invest?", "should i invest"}:
                    return (
                        True,
                        "Missing investment target",
                        "What are you considering investing in—stocks, mutual funds, an SIP, or something else?",
                    )
                elif q_lower in {"what is it?", "what is it", "is it safe?", "is it safe", "is it good?", "is it good"}:
                    return (
                        True,
                        "Unresolved pronoun reference",
                        "Could you specify what topic, scheme, or investment you are referring to?",
                    )
                elif q_lower in {"how much?", "how much"}:
                    return (
                        True,
                        "Missing financial subject",
                        "Could you specify what you would like to measure or check (e.g. monthly spending, SIP investment, or emergency fund)?",
                    )

        # Check unresolved pronoun reference in longer queries
        if conv_reference and conv_reference.confidence == 0.0 and conv_reference.resolved_target == "UNKNOWN":
            return (
                True,
                "Unresolved pronoun reference",
                f"Could you specify what product or topic you mean by '{conv_reference.pronoun}'?",
            )

        return False, None, None

    def detect_operation(
        self, q_lower: str, intent: QueryIntent, comparison_info: ComparisonInfo
    ) -> OperationType:
        """Detect operation type requested by user."""
        if any(kw in q_lower for kw in self.TRANSACTIONAL_KEYWORDS):
            return OperationType.ACTION_REQUEST

        if comparison_info.is_comparison:
            return OperationType.COMPARE

        if any(w in q_lower for w in ["how should i build", "how to build", "how can i build", "plan for", "retirement plan"]):
            return OperationType.PLAN

        if any(
            w in q_lower
            for w in [
                "how much did i spend",
                "how much in savings",
                "what is my net worth",
                "my net worth",
                "my balance",
                "total spent",
                "how much did i invest",
                "how much do i have",
                "how much have i invested",
                "gold price",
                "nifty",
            ]
        ):
            return OperationType.LOOKUP

        if any(w in q_lower for w in ["what is", "definition of", "meaning of", "kya hai", "kya hota hai"]):
            return OperationType.DEFINE

        if any(w in q_lower for w in ["calculate", "formula", "how is emi calculated", "how is interest calculated"]):
            return OperationType.CALCULATE

        if any(w in q_lower for w in ["why am i overspending", "is my savings rate healthy", "am i saving enough", "why"]):
            return OperationType.ANALYZE

        if any(w in q_lower for w in ["should i", "where to invest", "recommend", "best mutual fund"]):
            return OperationType.RECOMMEND

        if any(w in q_lower for w in ["is my goal affordable", "can i afford"]):
            return OperationType.CHECK

        if any(w in q_lower for w in ["explain", "how does", "details on"]):
            return OperationType.EXPLAIN

        return OperationType.EXPLAIN

    def classify_scope(
        self,
        q_clean: str,
        q_lower: str,
        intent: QueryIntent,
        sub_intent: SubIntent,
        operation: OperationType,
        comparison_info: ComparisonInfo,
        clarification_required: bool,
    ) -> QueryScope:
        """Classify overall query scope."""
        if clarification_required:
            return QueryScope.AMBIGUOUS

        if intent == QueryIntent.CASUAL:
            return QueryScope.CASUAL

        if operation == OperationType.ACTION_REQUEST:
            return QueryScope.TRANSACTIONAL

        if any(kw in q_lower for kw in self.MARKET_KEYWORDS):
            return QueryScope.MARKET_INFORMATION

        if comparison_info.is_comparison:
            return QueryScope.COMPARISON

        if (
            sub_intent in (SubIntent.FINANCIAL_PLANNING, SubIntent.GOAL_ANALYSIS)
            or operation == OperationType.PLAN
            or any(w in q_lower for w in ["for retirement", "save for", "build an emergency fund", "emergency fund"])
        ):
            return QueryScope.PLANNING

        # Mixed queries check (combines personal analysis and educational/planning)
        if intent == QueryIntent.MIXED or ("is my" in q_lower and "how" in q_lower):
            return QueryScope.MIXED

        if intent == QueryIntent.PERSONAL_FINANCE and operation == OperationType.LOOKUP:
            return QueryScope.PERSONAL_LOOKUP

        if intent == QueryIntent.PERSONAL_FINANCE:
            return QueryScope.PERSONAL_ANALYSIS

        if intent == QueryIntent.GENERAL_FINANCE:
            return QueryScope.EDUCATIONAL

        return QueryScope.EDUCATIONAL

    def assign_entity_roles(
        self,
        q_lower: str,
        entities: List[ExtractedEntity],
        comparison_info: ComparisonInfo,
        intent: QueryIntent,
        scope: QueryScope,
    ) -> Dict[str, EntityRole]:
        """Assign explicit roles to extracted domain entities."""
        roles: Dict[str, EntityRole] = {}
        if not entities:
            return roles

        if comparison_info.is_comparison and len(entities) >= 2:
            roles[entities[0].value] = EntityRole.COMPARISON_LEFT
            roles[entities[1].value] = EntityRole.COMPARISON_RIGHT
            for e in entities[2:]:
                roles[e.value] = EntityRole.OTHER
            return roles

        for e in entities:
            val_lower = e.value.lower()
            raw_lower = e.raw_text.lower()

            if scope == QueryScope.PERSONAL_LOOKUP or any(w in q_lower for w in ["how much in ", "invest in " + raw_lower, "in " + raw_lower, "in " + val_lower]):
                if "how much" in q_lower:
                    roles[e.value] = EntityRole.FILTER
                else:
                    roles[e.value] = EntityRole.INVESTMENT_TARGET
            elif any(w in q_lower for w in ["my " + raw_lower, "my " + val_lower]):
                roles[e.value] = EntityRole.PERSONAL_INVESTMENT
            elif scope == QueryScope.EDUCATIONAL or "what is" in q_lower:
                roles[e.value] = EntityRole.SUBJECT
            else:
                roles[e.value] = EntityRole.SUBJECT
                roles[e.value] = EntityRole.SUBJECT

        return roles

    def detect_personalization_level(
        self,
        q_lower: str,
        intent: QueryIntent,
        scope: QueryScope,
        entities: List[ExtractedEntity],
    ) -> PersonalizationLevel:
        """Determine personalization level required by the user query."""
        if any(w in q_lower for w in ["for me", "my ", "i ", "mine", "am i", "should i"]):
            return PersonalizationLevel.HIGH

        if scope in (QueryScope.PERSONAL_LOOKUP, QueryScope.PERSONAL_ANALYSIS):
            return PersonalizationLevel.HIGH

        if scope == QueryScope.PLANNING:
            return PersonalizationLevel.HIGH if "my" in q_lower else PersonalizationLevel.MEDIUM

        if scope == QueryScope.COMPARISON:
            return PersonalizationLevel.HIGH if "my" in q_lower or "should i" in q_lower else PersonalizationLevel.LOW

        if any(w in q_lower for w in ["good", "best", "should", "worth"]):
            return PersonalizationLevel.LOW

        if scope == QueryScope.EDUCATIONAL or intent == QueryIntent.CASUAL:
            return PersonalizationLevel.NONE

        return PersonalizationLevel.NONE

    def determine_data_sources(
        self,
        scope: QueryScope,
        intent: QueryIntent,
        q_lower: str,
        personalization_level: PersonalizationLevel,
        clarification_required: bool,
        history: Optional[List],
    ) -> Tuple[bool, bool, bool, bool, bool, bool]:
        """
        100% Deterministic Source Selection logic.

        Returns:
            (requires_rag, requires_financial_engine, requires_market_data,
             requires_conversation_context, requires_user_profile, requires_document_context)
        """
        # If clarification is required, block expensive data retrieval!
        if clarification_required:
            return False, False, False, (history is not None and len(history) > 0), False, False

        requires_rag = (
            scope in (
                QueryScope.EDUCATIONAL,
                QueryScope.COMPARISON,
                QueryScope.PLANNING,
                QueryScope.MIXED,
                QueryScope.AMBIGUOUS,
            )
            or (scope == QueryScope.PERSONAL_ANALYSIS and any(w in q_lower for w in ["sip", "ppf", "elss", "mutual fund", "tax", "loan", "80c", "nps", "fd", "rd", "invest", "stock", "bond", "insurance"]))
            or intent in (QueryIntent.GENERAL_FINANCE, QueryIntent.MIXED)
        ) and scope not in (QueryScope.MARKET_INFORMATION, QueryScope.PERSONAL_LOOKUP)

        requires_fe = scope in (
            QueryScope.PERSONAL_LOOKUP,
            QueryScope.PERSONAL_ANALYSIS,
            QueryScope.MIXED,
            QueryScope.PLANNING,
        ) or personalization_level == PersonalizationLevel.HIGH or intent in (
            QueryIntent.PERSONAL_FINANCE,
            QueryIntent.MIXED,
        )

        requires_market = scope == QueryScope.MARKET_INFORMATION or any(
            kw in q_lower for kw in self.MARKET_KEYWORDS
        )

        requires_conv = history is not None and len(history) > 0

        requires_profile = personalization_level in (
            PersonalizationLevel.MEDIUM,
            PersonalizationLevel.HIGH,
        )

        requires_doc = any(
            w in q_lower for w in ["document", "pdf", "statement", "uploaded", "file", "tax form"]
        )

        return (
            requires_rag,
            requires_fe,
            requires_market,
            requires_conv,
            requires_profile,
            requires_doc,
        )
