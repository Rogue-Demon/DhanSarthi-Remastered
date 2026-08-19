"""
Intelligent Retrieval Query Rewriter for DhanSarthi Phase L.3.

Provides deterministic, local, lightweight, and explainable query rewriting
optimized for pgvector similarity search without LLM overhead or network calls.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.ai.router import QueryIntent
from app.ai.schemas.query_execution_plan import OperationType, QueryExecutionPlan, QueryScope
from app.ai.schemas.query_understanding import QueryUnderstanding


class RetrievalRewriteResult(BaseModel):
    """Structured result of retrieval query rewriting."""

    original_query: str
    resolved_query: str
    retrieval_query: str

    canonical_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[str] = Field(default_factory=list)
    entity_terms: List[str] = Field(default_factory=list)
    intent_terms: List[str] = Field(default_factory=list)
    temporal_terms: List[str] = Field(default_factory=list)
    excluded_terms: List[str] = Field(default_factory=list)

    rewrite_applied: bool = False
    rewrite_reason: str = "Standard expansion"
    confidence: float = 1.0


class RetrievalQueryRewriter:
    """
    Deterministic Retrieval Query Rewriter.
    
    Transforms user inputs into high-density vector search queries while
    preserving original user text for UI display and LLM context.
    """

    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"forget\s+(?:all\s+)?rules",
        r"act\s+as\s+a?\s*dan",
        r"bypass\s+safety",
        r"disregard\s+system\s+prompt",
        r"you\s+are\n+now\s+unrestricted",
    ]

    FILLER_PATTERNS = [
        r"\b(hey|hello|hi)\b",
        r"\bcan\s+you\s+(?:please\s+)?tell\s+me\b",
        r"\bplease\s+(?:tell|explain)\s+(?:me\s+)?\b",
        r"\bi\s+want\s+to\s+know\b",
        r"\bactually\b",
        r"\bjust\s+wanted\s+to\s+know\b",
    ]

    INTENT_TERM_MAP = {
        "risk": ["investment risk", "risk factors", "market risk", "volatility"],
        "risks": ["investment risk", "risk factors", "market risk", "volatility"],
        "tax": ["tax rules", "tax implications", "tax deduction", "taxable income"],
        "return": ["expected returns", "historical returns", "yield", "compounding"],
        "returns": ["expected returns", "historical returns", "yield", "compounding"],
        "safety": ["safety", "risk level", "capital protection", "guarantee"],
    }

    def __init__(self, terms_filepath: Optional[str] = None) -> None:
        if terms_filepath is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            terms_filepath = str(base_dir / "data" / "knowledge" / "query_terms.json")

        self.terms_filepath = terms_filepath
        self._dictionary: Dict[str, Dict[str, Any]] = self._load_dictionary()

    def _load_dictionary(self) -> Dict[str, Dict[str, Any]]:
        path = Path(self.terms_filepath)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def rewrite(
        self,
        understanding: QueryUnderstanding,
        execution_plan: Optional[QueryExecutionPlan] = None,
    ) -> RetrievalRewriteResult:
        """
        Rewrite query for optimal vector search.
        
        Args:
            understanding: QueryUnderstanding payload from Phase L.1.
            execution_plan: QueryExecutionPlan payload from Phase L.2.

        Returns:
            RetrievalRewriteResult with structured terms and final retrieval_query string.
        """
        orig_query = understanding.original_query
        res_query = understanding.resolved_query or orig_query
        corr_query = understanding.corrected_query or res_query
        plan = execution_plan or understanding.execution_plan

        excluded_terms: List[str] = []

        # 1. Prompt Injection Defense Filtering
        clean_text = corr_query
        for inj_pat in self.PROMPT_INJECTION_PATTERNS:
            match = re.search(inj_pat, clean_text, re.IGNORECASE)
            if match:
                excluded_terms.append(match.group(0))
                clean_text = re.sub(inj_pat, "", clean_text, flags=re.IGNORECASE)

        # 2. Filler Noise Removal
        for fill_pat in self.FILLER_PATTERNS:
            clean_text = re.sub(fill_pat, "", clean_text, flags=re.IGNORECASE)

        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Deduplicate repeated word tokens in clean_text
        clean_words = []
        seen_clean_words = set()
        for w in clean_text.split():
            w_lower = w.lower()
            if w_lower not in seen_clean_words:
                seen_clean_words.add(w_lower)
                clean_words.append(w)
        clean_text = " ".join(clean_words)

        # 3. Canonical Term Expansion
        canonical_terms, expanded_terms = self._expand_dictionary_terms(clean_text)

        # 4. Entity Terms
        entity_terms: List[str] = []
        for entity in understanding.entities:
            # Exclude monetary numbers from vector search string
            if entity.entity_type.value != "amount":
                if entity.value not in entity_terms:
                    entity_terms.append(entity.value)

        # 5. Intent & Scope Specific Terms
        intent_terms: List[str] = []
        q_lower = clean_text.lower()

        for kw, terms in self.INTENT_TERM_MAP.items():
            if kw in q_lower:
                for t in terms:
                    if t not in intent_terms:
                        intent_terms.append(t)

        if plan:
            if plan.operation == OperationType.DEFINE or "what is" in q_lower:
                intent_terms.extend(["definition", "how it works", "features"])
            elif plan.operation == OperationType.COMPARE or plan.comparison_info.is_comparison:
                intent_terms.extend(["comparison", "risk", "returns", "liquidity", "tax"])
            elif plan.operation == OperationType.RECOMMEND or "should i" in q_lower:
                intent_terms.extend(["investment suitability", "risks", "benefits", "considerations"])
            elif plan.scope == QueryScope.PLANNING:
                intent_terms.extend(["financial planning", "savings strategy"])
            elif plan.scope == QueryScope.PERSONAL_ANALYSIS or "savings rate" in q_lower:
                intent_terms.extend(["savings rate", "personal finance", "financial planning", "healthy savings rate", "benchmarks"])

        # 6. Temporal Terms
        temporal_terms: List[str] = []
        for t_ref in understanding.temporal_references:
            if t_ref.expression not in temporal_terms:
                temporal_terms.append(t_ref.expression)
            if t_ref.is_historical and "historical rules" not in temporal_terms:
                temporal_terms.append("historical rules")

        # 7. Token-Level Deduplication & Bounded Construction
        seen_words: Set[str] = set()
        final_terms: List[str] = []

        all_candidates = [clean_text] + canonical_terms + entity_terms + temporal_terms + intent_terms + expanded_terms

        for chunk in all_candidates:
            if not chunk or not chunk.strip():
                continue
            chunk_words = chunk.strip().split()
            # Filter out any word that has already been seen in final_terms
            unseen = [w for w in chunk_words if w.lower() not in seen_words]
            if unseen:
                for w in chunk_words:
                    seen_words.add(w.lower())
                final_terms.append(" ".join(chunk_words))

        # Length Bounding (max 12 unique term chunks or max 250 characters)
        bounded_terms = final_terms[:12]
        final_retrieval_query = " ".join(bounded_terms)
        if len(final_retrieval_query) > 250:
            final_retrieval_query = final_retrieval_query[:250].rsplit(" ", 1)[0]

        rewrite_applied = final_retrieval_query.lower() != orig_query.lower()

        return RetrievalRewriteResult(
            original_query=orig_query,
            resolved_query=res_query,
            retrieval_query=final_retrieval_query,
            canonical_terms=canonical_terms,
            expanded_terms=expanded_terms,
            entity_terms=entity_terms,
            intent_terms=list(set(intent_terms)),
            temporal_terms=temporal_terms,
            excluded_terms=excluded_terms,
            rewrite_applied=rewrite_applied,
            rewrite_reason="Intent & entity aware canonical expansion",
            confidence=1.0,
        )

    def _expand_dictionary_terms(self, text: str) -> Tuple[List[str], List[str]]:
        """Expand terms using query_terms.json."""
        if not text or not self._dictionary:
            return [], []

        canonical_terms: List[str] = []
        expanded_terms: List[str] = []
        query_tokens = set(text.lower().split())

        for key, entry in self._dictionary.items():
            synonyms = entry.get("synonyms", [])
            canonical = entry.get("canonical", "")
            expansions = entry.get("expanded_terms", [])

            matched = False
            for syn in synonyms:
                syn_lower = syn.lower()
                if len(syn_lower) <= 2:
                    if syn_lower in query_tokens:
                        matched = True
                        break
                elif re.search(r"\b" + re.escape(syn_lower) + r"\b", text, re.IGNORECASE):
                    matched = True
                    break

            if matched:
                if canonical and canonical not in canonical_terms:
                    canonical_terms.append(canonical)
                for exp in expansions:
                    if exp not in expanded_terms:
                        expanded_terms.append(exp)

        return canonical_terms, expanded_terms
