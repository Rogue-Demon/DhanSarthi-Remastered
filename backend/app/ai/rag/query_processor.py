""""
Query Processor for DhanSarthi RAG Retrieval System.

Provides lightweight, explainable, and deterministic:
  1. Query Normalization (whitespace, punctuation, casing, Hinglish phrasing).
  2. Query Expansion (using financial term dictionary data/knowledge/query_terms.json).
  3. Historical Intent Detection (detects tax year / FY / AY / historical markers).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class QueryProcessor:
    """Deterministic Query Normalizer and Term Expander."""

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

    def process(self, query: str) -> Tuple[str, str, List[str], bool, Optional[str]]:
        """
        Process query into (original_query, normalized_query, expanded_terms, is_historical, target_year).
        """
        original_query = query
        normalized = self.normalize(query)
        expanded_terms = self.expand_query(normalized)
        is_historical, target_year = self.detect_historical_intent(query)

        return original_query, normalized, expanded_terms, is_historical, target_year

    def normalize(self, query: str) -> str:
        """
        Normalize query string:
        - Strip whitespace and collapse multiple spaces.
        - Lowercase for matching.
        - Clean punctuation.
        - Replace common Hinglish / casual question suffixes ("kya hai", "kya hota hai", etc.).
        """
        if not query:
            return ""

        text = query.strip()

        # Remove trailing question marks / punctuation for normalization
        clean_text = re.sub(r"[?!.,;:]+", " ", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Lowercase for canonical matching
        lower = clean_text.lower()

        # Common Hinglish phrases normalization
        lower = re.sub(r"\b(kya hai|kya hota hai|kya h|matlab kya hai|batao|bataiye)\b", "", lower).strip()
        lower = re.sub(r"\b(rules and regulations|rules|guidelines|meaning|details|definition)\b", "", lower).strip()
        lower = re.sub(r"\s+", " ", lower).strip()

        return lower

    def expand_query(self, normalized_query: str) -> List[str]:
        """
        Map terms in normalized_query to expanded financial concepts from query_terms.json.
        """
        if not normalized_query or not self._dictionary:
            return [normalized_query] if normalized_query else []

        expanded_set = set()
        expanded_set.add(normalized_query)

        query_tokens = set(normalized_query.lower().split())

        for key, entry in self._dictionary.items():
            synonyms = entry.get("synonyms", [])
            canonical = entry.get("canonical", "")
            expanded_terms = entry.get("expanded_terms", [])

            # Check if any synonym matches normalized query with word boundaries
            matched = False
            for syn in synonyms:
                syn_lower = syn.lower()
                if len(syn_lower) <= 2:
                    if syn_lower in query_tokens:
                        matched = True
                        break
                elif re.search(r"\b" + re.escape(syn_lower) + r"\b", normalized_query, re.I):
                    matched = True
                    break

            if matched:
                expanded_set.add(canonical)
                for exp in expanded_terms:
                    expanded_set.add(exp)

        return list(expanded_set)

    def detect_historical_intent(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detect whether a query asks about historical rules, previous tax years, or past regulations.
        """
        if not query:
            return False, None

        q_lower = query.lower()

        # Match explicit FY / AY patterns
        fy_match = re.search(r"\b(fy|ay|financial year|assessment year)\s*(\d{4}[-\s]?\d{2,4})\b", q_lower)
        if fy_match:
            year_str = fy_match.group(2)
            # If asking about past years (e.g., 2024, 2023, 2022)
            if "2024" in year_str or "2023" in year_str or "2022" in year_str or "2021" in year_str:
                return True, fy_match.group(0)

        # Match historical keywords
        historical_keywords = [
            "previous rule",
            "old rule",
            "earlier rule",
            "at that time",
            "historical",
            "in 2024",
            "in 2023",
            "in 2022",
            "in 2020",
            "before 2025",
            "old tax regime slabs",
        ]

        for kw in historical_keywords:
            if kw in q_lower:
                return True, kw

        return False, None
