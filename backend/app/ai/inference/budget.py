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


class PersonalFastPathClassifier:
    """
    Deterministic classifier for Phase L.11.2 Personal Fast-Path.
    
    Determines whether an incoming query is a direct personal-finance lookup
    eligible for RAG bypass, market-data bypass, minimal context, and reduced token budget (<= 180 tokens).
    
    Signals evaluated (no fragile regexes):
      - QueryIntent (PERSONAL_FINANCE / MIXED with primary personal lookup)
      - QueryExecutionPlan scope (PERSONAL_LOOKUP)
      - QueryExecutionPlan operation (LOOKUP, CHECK, TRACK, SUMMARIZE, EXPLAIN)
      - Non-comparison (not comparison_info.is_comparison)
      - Non-historical (no historical temporal references)
      - Non-planning, non-recommendation
      - No clarification needed
      - Not requiring external general RAG or live market rates
    """

    @staticmethod
    def is_personal_fast_path(
        intent: Optional[QueryIntent],
        execution_plan: Optional[Any],
        sub_intent: Optional[Any] = None,
        temporal_references: Optional[list] = None,
        query: Optional[str] = None,
    ) -> tuple[bool, Optional[str], int]:
        """
        Evaluate if query qualifies for personal fast-path.
        
        Returns:
            (is_fast_path, fast_path_reason, token_budget)
        """
        if not execution_plan:
            return False, None, 0

        scope = getattr(execution_plan, "scope", None)
        scope_str = scope.value if hasattr(scope, "value") else str(scope or "")
        op = getattr(execution_plan, "operation", None)
        op_str = op.value if hasattr(op, "value") else str(op or "")

        # Disqualify if clarification required
        if getattr(execution_plan, "clarification_required", False):
            return False, None, 0

        # Disqualify if comparison query
        comp_info = getattr(execution_plan, "comparison_info", None)
        if comp_info and getattr(comp_info, "is_comparison", False):
            return False, None, 0

        # Disqualify if historical reference (e.g. "what was my spending last year?")
        if temporal_references and any(getattr(t, "is_historical", False) for t in temporal_references):
            return False, None, 0

        # Disqualify if planning or recommendation operation
        if op_str in ("PLAN", "PLANNING", "RECOMMEND", "PREDICT"):
            return False, None, 0

        # Disqualify if query requires general RAG or market data
        if getattr(execution_plan, "requires_rag", False) or getattr(execution_plan, "requires_market_data", False):
            return False, None, 0

        # Check for direct personal lookup scope or personal intent with lookup operation
        if scope_str == "PERSONAL_LOOKUP" or (
            intent == QueryIntent.PERSONAL_FINANCE and op_str in ("LOOKUP", "CHECK", "TRACK", "SUMMARIZE", "EXPLAIN")
        ):
            q_clean = (query or "").lower().strip()
            
            # Select target token budget based on explanation depth requested
            if any(kw in q_clean for kw in ["explain in detail", "breakdown in detail", "long explanation", "explain fully"]):
                return True, "LONGER_PERSONAL_EXPLANATION", 180
            elif any(kw in q_clean for kw in ["why", "explain", "how come", "describe", "details"]):
                return True, "DIRECT_LOOKUP_WITH_EXPLANATION", 160
            else:
                return True, "DIRECT_PERSONAL_LOOKUP", 128

        return False, None, 0


class BalancedWorkloadCategory:
    """Workload categories within the BALANCED inference tier for Phase L.11.5."""
    SHORT_DEFINITION = "SHORT_DEFINITION"  # 128-180 tokens, 1-2 RAG chunks
    TAX_REGULATORY = "TAX_REGULATORY"      # 160-220 tokens, 2-3 RAG chunks
    COMPARISON = "COMPARISON"              # 220-320 tokens, 2-4 RAG chunks
    BANKING = "BANKING"                    # 128-180 tokens, 1-2 RAG chunks
    HISTORICAL = "HISTORICAL"              # 320-512 tokens, 3-4 RAG chunks
    GENERAL = "GENERAL"                    # 200-300 tokens, 2-3 RAG chunks


class BalancedWorkloadClassifier:
    """
    Deterministic classifier for Phase L.11.5 Balanced-Tier Real Inference Optimization.
    
    Determines fine-grained workload characteristics for BALANCED queries to assign
    tightly-bounded output token budgets and optimal RAG chunk counts.
    """

    @staticmethod
    def classify(
        query: str,
        intent: Optional[QueryIntent] = None,
        execution_plan: Optional[Any] = None,
        sub_intent: Optional[Any] = None,
        temporal_references: Optional[list] = None,
    ) -> tuple[str, int, int]:
        """
        Classify BALANCED workload.
        
        Returns:
            (category, token_budget, max_rag_chunks)
        """
        q_clean = (query or "").lower().strip()
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else ""
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else ""
        is_comparison = bool(execution_plan and execution_plan.comparison_info and execution_plan.comparison_info.is_comparison)
        is_historical = bool(temporal_references and any(getattr(t, "is_historical", False) for t in temporal_references))

        # Check if tax/regulatory
        is_tax = False
        if execution_plan and getattr(execution_plan, "entities", None):
            is_tax = any(
                getattr(e, "entity_type", None) and getattr(e.entity_type, "value", "") == "tax_category"
                for e in execution_plan.entities
            )
        if any(kw in q_clean for kw in ["80c", "tax", "tds", "gst", "section", "income tax", "capital gains"]):
            is_tax = True

        # Check if banking definition
        is_banking = any(kw in q_clean for kw in ["emi", "savings account", "current account", "neft", "rtgs", "imps", "upi", "cheque", "overdraft"])

        # 1. Comparison queries (e.g. "SIP vs FD which is better?") -> 220-300 tokens, 2-4 chunks
        if is_comparison or op_str == "COMPARE" or scope_str == "COMPARISON" or " vs " in q_clean or "compare" in q_clean:
            return BalancedWorkloadCategory.COMPARISON, 300, 3

        # 2. Tax & Regulatory explanations (e.g. "what is Section 80C?") -> 180-220 tokens, 2-3 chunks
        if is_tax:
            return BalancedWorkloadCategory.TAX_REGULATORY, 220, 3

        # 3. Banking product definitions (e.g. "what is an EMI?") -> 160-180 tokens, 1-2 chunks
        if is_banking and len(q_clean.split()) < 12:
            return BalancedWorkloadCategory.BANKING, 160, 2

        # 4. Historical analysis -> 384 tokens, 3-4 chunks
        if is_historical or scope_str == "PERSONAL_ANALYSIS":
            return BalancedWorkloadCategory.HISTORICAL, 384, 4

        # 5. Short educational definition (e.g. "what is an FD?", "what is compound interest?", "what is a mutual fund?") -> 160-180 tokens, 1-2 chunks
        if intent == QueryIntent.GENERAL_FINANCE and (len(q_clean.split()) < 10 or op_str in ("EXPLAIN", "LOOKUP")):
            return BalancedWorkloadCategory.SHORT_DEFINITION, 180, 2

        # 6. Default general finance
        return BalancedWorkloadCategory.GENERAL, 256, 3


class ReasoningWorkloadCategory:
    """Workload categories within the REASONING inference tier for Phase L.11.6."""
    COMPLEX_SIMPLE = "COMPLEX_SIMPLE"          # 384–512 tokens (e.g. debt repayment overview, emergency fund allocation)
    COMPLEX_ANALYSIS = "COMPLEX_ANALYSIS"      # 512–640 tokens (e.g. multi-goal asset allocation, portfolio rebalancing)
    DEEP_PLANNING = "DEEP_PLANNING"            # 640–768 tokens (e.g. multi-decade retirement planning, holistic financial roadmap)
    REGULATORY_COMPLEX = "REGULATORY_COMPLEX"  # 640–768 tokens (e.g. tax-aware multi-instrument planning)


class ReasoningWorkloadClassifier:
    """
    Deterministic classifier for Phase L.11.6 Reasoning-Tier Inference Optimization.
    
    Determines fine-grained complexity and required output depth for REASONING workloads.
    """

    @staticmethod
    def classify(
        query: str,
        intent: Optional[QueryIntent] = None,
        execution_plan: Optional[Any] = None,
        sub_intent: Optional[Any] = None,
        temporal_references: Optional[list] = None,
    ) -> tuple[str, int, int]:
        """
        Classify REASONING workload.
        
        Returns:
            (category, token_budget, max_rag_chunks)
        """
        q_clean = (query or "").lower().strip()
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else ""
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else ""

        # Check for deep multi-decade retirement / comprehensive financial roadmap
        is_deep_planning = any(
            kw in q_clean for kw in [
                "retirement", "retire", "long-term", "decade", "pension",
                "corpus", "holistic", "roadmap", "financial independence", "fire"
            ]
        ) or (scope_str == "PLANNING" and op_str == "PLAN")

        # Check for complex tax-aware multi-instrument planning
        is_regulatory_complex = any(
            kw in q_clean for kw in ["tax-loss", "harvesting", "capital gains", "80c", "regime", "tax planning", "tax-aware"]
        ) and (op_str in ("PLAN", "PLANNING", "RECOMMEND") or "plan" in q_clean)

        # Check for focused complex simple queries (e.g. single debt strategy, single goal calculation)
        is_complex_simple = any(
            kw in q_clean for kw in [
                "emergency fund", "debt snowball", "debt avalanche", "pay off loan", "loan payoff",
                "sip allocation", "how much sip"
            ]
        ) and not is_deep_planning

        if is_deep_planning:
            return ReasoningWorkloadCategory.DEEP_PLANNING, 768, 5
        elif is_regulatory_complex:
            return ReasoningWorkloadCategory.REGULATORY_COMPLEX, 768, 4
        elif is_complex_simple:
            return ReasoningWorkloadCategory.COMPLEX_SIMPLE, 512, 3
        else:
            # Default complex multi-goal / portfolio analysis
            return ReasoningWorkloadCategory.COMPLEX_ANALYSIS, 640, 4


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
        budget = self._select_token_budget(
            intent=intent,
            execution_plan=execution_plan,
            complexity=complexity,
            sub_intent=sub_intent,
            temporal_references=temporal_references,
            query=query,
        )

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
        sub_intent: Optional[Any] = None,
        temporal_references: Optional[list] = None,
        query: Optional[str] = None,
    ) -> int:
        """Select output token budget bounded by settings.ai_max_tokens and global safety ceiling."""
        scope_str = execution_plan.scope.value if (execution_plan and execution_plan.scope) else None
        op_str = execution_plan.operation.value if (execution_plan and execution_plan.operation) else None

        # 1. Phase L.11.2: Check Personal Fast-Path Budget First (128-180 tokens)
        is_fp, fp_reason, fp_budget = PersonalFastPathClassifier.is_personal_fast_path(
            intent=intent,
            execution_plan=execution_plan,
            sub_intent=sub_intent,
            temporal_references=temporal_references,
            query=query,
        )
        if is_fp:
            raw_budget = fp_budget

        # 2. Casual queries (128 tokens)
        elif intent == QueryIntent.CASUAL:
            raw_budget = getattr(settings, "ai_max_tokens_casual", 128)

        # 3. Complex planning & Multi-step strategy (Phase L.11.6 Reasoning Optimization)
        elif op_str in ("PLAN", "PLANNING", "RECOMMEND", "PREDICT") or complexity == InferenceComplexity.COMPLEX or scope_str == "PLANNING":
            r_cat, r_budget, _ = ReasoningWorkloadClassifier.classify(
                query=query or "",
                intent=intent,
                execution_plan=execution_plan,
                sub_intent=sub_intent,
                temporal_references=temporal_references,
            )
            raw_budget = r_budget

        # 4. Phase L.11.5: Fine-Grained BALANCED Tier Workload Budgeting
        else:
            cat, cat_budget, _ = BalancedWorkloadClassifier.classify(
                query=query or "",
                intent=intent,
                execution_plan=execution_plan,
                sub_intent=sub_intent,
                temporal_references=temporal_references,
            )
            raw_budget = cat_budget

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
