"""
LLM Context Optimizer for Phase L.7.4.

Determines which context components (system instructions, user facts, RAG knowledge,
conversation history, market data) reach the LLM and enforces character limits and
priority order.
NO LLM calls are made for context optimization.
"""

from __future__ import annotations

import json
import logging
from typing import Any, List, Optional, Tuple

from app.ai.inference.config import InferenceComplexity, InferenceConfig
from app.ai.router import QueryIntent
from app.ai.schemas.advisor import AIContext, RetrievedDocument
from app.core.config import settings

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN_ESTIMATE: float = 4.0


class LLMContextOptimizer:
    """Optimizes input prompt payloads and conversation history for LLM consumption."""

    def optimize_history(
        self,
        history: List[Any],
        config: InferenceConfig,
        intent: Optional[QueryIntent] = None,
    ) -> List[Any]:
        """
        Filter conversation history messages according to adaptive limit and character budget.
        Does not mutate message contents.
        """
        if not history:
            return []

        # 1. Limit message count by adaptive history_limit
        max_msgs = config.history_limit
        recent = history[-max_msgs:] if len(history) > max_msgs else list(history)

        # 2. Enforce character limit (AI_MAX_HISTORY_CHARS)
        max_chars = config.max_history_chars
        total_chars = sum(len(getattr(m, "content", "") or "") for m in recent)

        if total_chars > max_chars:
            # Retain most recent messages while staying within character budget
            trimmed: List[Any] = []
            curr_chars = 0
            for m in reversed(recent):
                m_len = len(getattr(m, "content", "") or "")
                if curr_chars + m_len <= max_chars or not trimmed:
                    trimmed.insert(0, m)
                    curr_chars += m_len
                else:
                    break
            return trimmed

        return recent

    def optimize_rag_docs(
        self,
        docs: List[RetrievedDocument],
        config: InferenceConfig,
        intent: Optional[QueryIntent] = None,
        is_comparison: bool = False,
        workload_category: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        """
        Select relevant RAG knowledge chunks and enforce character budget.
        Preserves document citation identity metadata (document_id, title, source, authority, source_url).
        """
        if not docs:
            return []

        # 1. Determine target document count based on query complexity/intent/workload
        if intent in (QueryIntent.CASUAL, QueryIntent.PERSONAL_FINANCE):
            return []  # CASUAL and pure PERSONAL_FINANCE do not use RAG context

        if workload_category in ("SHORT_DEFINITION", "BANKING"):
            target_count = 2  # Concise 1-2 authoritative sources for simple definitions
        elif workload_category == "TAX_REGULATORY":
            target_count = 3  # 2-3 authoritative sources for tax & regulatory rules
        elif is_comparison or workload_category == "COMPARISON":
            target_count = 3  # 2-3 sources for direct entity comparisons
        elif workload_category == "COMPLEX_SIMPLE":
            target_count = 3  # 3 authoritative sources for focused complex queries
        elif workload_category == "COMPLEX_ANALYSIS":
            target_count = 4  # 4 sources for multi-goal / portfolio analysis
        elif workload_category in ("DEEP_PLANNING", "REGULATORY_COMPLEX"):
            target_count = min(len(docs), 5)  # Up to 5 comprehensive sources for deep planning
        elif config.complexity == InferenceComplexity.SIMPLE and not is_comparison:
            target_count = 2  # Prefer strongest 1-2 sources for simple definitions
        elif is_comparison:
            target_count = 4  # Allow 3-4 sources for comparisons
        else:
            target_count = min(len(docs), 4)

        selected = docs[:target_count]

        # 2. Enforce character limit (AI_MAX_RAG_CONTEXT_CHARS)
        max_rag_chars = config.max_rag_context_chars
        result: List[RetrievedDocument] = []
        curr_chars = 0

        for doc in selected:
            content_len = len(doc.content or "")
            if curr_chars + content_len <= max_rag_chars or not result:
                result.append(doc)
                curr_chars += content_len
            else:
                break

        return result

    def should_include_personal_context(
        self,
        intent: Optional[QueryIntent],
        config: InferenceConfig,
    ) -> bool:
        """Determine whether user personal financial context should be included."""
        if intent in (QueryIntent.CASUAL, QueryIntent.GENERAL_FINANCE):
            return False
        return True

    def should_include_market_data(
        self,
        requires_market_data: bool,
    ) -> bool:
        """Market data is ONLY included when explicitly required by execution plan."""
        return requires_market_data

    def estimate_tokens(self, prompt: str, max_tokens: int) -> Tuple[int, int, int]:
        """
        Calculate lightweight character-ratio token estimates for prompt, response, and total workload.
        """
        prompt_chars = len(prompt)
        estimated_prompt_tokens = int(prompt_chars / CHARS_PER_TOKEN_ESTIMATE)
        estimated_output_tokens = max_tokens
        estimated_total_tokens = estimated_prompt_tokens + estimated_output_tokens
        return estimated_prompt_tokens, estimated_output_tokens, estimated_total_tokens
