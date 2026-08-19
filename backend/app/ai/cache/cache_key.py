"""
Phase L.9.6 — Deterministic Cache Key Generator for DhanSarthi AI Advisor.

Builds canonical SHA-256 cache keys incorporating query normalization,
model routing ID, prompt version, and knowledge base version.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from app.core.config import settings


_PUNCTUATION_STRIP_PATTERN = re.compile(r"[^\w\s\d\-_\u0900-\u097F]")


class CacheKeyBuilder:
    """
    Constructs deterministic, canonical cache keys for AI response caching.
    """

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """
        Normalize query string:
        - Lowercase
        - Strip leading/trailing whitespace
        - Remove extraneous trailing question marks/punctuation for semantic consistency
        - Collapse multiple whitespace into a single space
        """
        if not query:
            return ""
        q = query.strip().lower()
        # Remove surrounding quotes or punctuation
        q = _PUNCTUATION_STRIP_PATTERN.sub(" ", q)
        return " ".join(q.split())

    @classmethod
    def build_key(
        cls,
        query: str,
        model_id: str,
        max_tokens_budget: int = 512,
        scope: Optional[str] = None,
        operation: Optional[str] = None,
        prompt_version: Optional[str] = None,
        knowledge_version: Optional[str] = None,
        policy_version: Optional[str] = None,
        cache_version: Optional[str] = None,
    ) -> str:
        """
        Construct a deterministic SHA-256 cache key string.

        Components:
          SHA256(
            normalized_query
            | scope
            | operation
            | model_id
            | prompt_version
            | knowledge_version
            | policy_version
            | cache_version
            | max_tokens_budget
          )
        """
        norm_query = cls.normalize_query(query)
        s_scope = (scope or "EDUCATIONAL").strip().upper()
        s_op = (operation or "EXPLAIN").strip().upper()
        s_model = (model_id or settings.ai_model).strip()
        s_prompt_v = (prompt_version or settings.ai_response_cache_prompt_version).strip()
        s_know_v = (knowledge_version or settings.ai_response_cache_knowledge_version).strip()
        s_pol_v = (policy_version or settings.ai_response_cache_policy_version).strip()
        s_cache_v = (cache_version or settings.ai_response_cache_version).strip()

        # Bucketize token budget to avoid cache fragmentation on minor budget variations
        # (e.g. 256, 512, 768, 1024)
        if max_tokens_budget <= 256:
            budget_bucket = 256
        elif max_tokens_budget <= 512:
            budget_bucket = 512
        elif max_tokens_budget <= 768:
            budget_bucket = 768
        else:
            budget_bucket = 1024

        canonical_str = (
            f"{norm_query}|{s_scope}|{s_op}|{s_model}|"
            f"{s_prompt_v}|{s_know_v}|{s_pol_v}|{s_cache_v}|{budget_bucket}"
        )

        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
