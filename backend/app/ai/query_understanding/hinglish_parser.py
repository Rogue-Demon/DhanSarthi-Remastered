"""
Financial Hinglish Parser for DhanSarthi Query Understanding Layer.

Normalizes common Indian financial Hinglish constructions to clean,
canonical financial search & reasoning forms while preserving user intent.
"""

from __future__ import annotations

import re
from typing import Tuple


class HinglishParser:
    """Deterministic Hinglish financial pattern normalizer."""

    # Hinglish pattern mappings to normalized English financial equivalents
    HINGLISH_PATTERNS = [
        # Conceptual questions
        (r"\b(sip|systematic investment plan)\s+(kya|kyaa)\s+(hota|h)\s+(hai|h)\b", "What is SIP?"),
        (r"\b(mf|mutual fund|mutual funds)\s+(kya|kyaa)\s+(hota|h)\s+(hai|h)\b", "What is a mutual fund?"),
        (r"\b(fd|fixed deposit)\s+safe\s+hai\s+(kya|kyaa)\b", "Is a fixed deposit safe?"),
        (r"\b(ppf|public provident fund)\s+(kya|kyaa)\s+(hai|h)\b", "What is PPF?"),
        (r"\b(nps|national pension system)\s+(kya|kyaa)\s+(hai|h)\b", "What is NPS?"),
        (r"\b(nav)\s+(kya|kyaa)\s+(hota|h)\s+(hai|h)\b", "What is NAV?"),
        (r"\b(emi)\s+kaise\s+(calculate|nikale)\s+(hota|h)\s+(hai|h)\b", "How is EMI calculated?"),
        (r"\bloan\s+ka\s+interest\s+kaise\s+calculate\s+hota\s+hai\b", "How is loan interest calculated?"),
        (r"\btax\s+kaise\s+(bachega|bachaye|kam\s+kare)\b", "What are the applicable ways to reduce tax?"),

        # Personal finance queries
        (r"\bmera\s+savings\s+rate\s+kaisa\s+hai\b", "How is my savings rate?"),
        (r"\bmera\s+(net\s+worth|total\s+worth)\s+kya\s+hai\b", "What is my net worth?"),
        (r"\bkitna\s+spend\s+kiya\b", "How much did I spend?"),
        (r"\bkitna\s+kharcha\s+huya\b", "How much did I spend?"),

        # Advice queries
        (r"\bmain\s+sip\s+me\s+invest\s+karu\??\b", "Should I consider investing in an SIP?"),
        (r"\bsip\s+me\s+invest\s+karu\s+kya\b", "Should I consider investing in an SIP?"),
    ]

    # Sub-phrase substitutions
    SUBPHRASE_MAP = [
        (r"\bkya\s+hota\s+hai\b", "definition and details"),
        (r"\bkya\s+hai\b", "definition and details"),
        (r"\bsafe\s+hai\s+kya\b", "safety and risk analysis"),
        (r"\bkaisa\s+hai\b", "performance analysis"),
        (r"\bkaise\s+bachega\b", "tax saving options"),
        (r"\bkaise\s+bachaye\b", "tax saving options"),
    ]

    def parse(self, text: str) -> Tuple[str, bool, str]:
        """
        Detect and normalize Hinglish financial phrases.

        Returns:
            (normalized_text, is_hinglish_detected, detected_language)
        """
        if not text or not text.strip():
            return text, False, "en"

        text_lower = text.strip().lower()

        # Check full pattern matches first
        for pattern, replacement in self.HINGLISH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return replacement, True, "hi-Latn"

        # Check for Hinglish markers (kya, hai, kaisa, mera, main, karu, kaise, kharcha)
        hinglish_markers = [
            "kya", "hai", "kaisa", "kaise", "mera", "meri", "main",
            "karu", "hote", "batao", "bataiye", "kharcha", "bachega"
        ]

        words = text_lower.split()
        marker_count = sum(1 for w in words if w in hinglish_markers)

        if marker_count >= 1:
            # Performs sub-phrase normalization
            working = text
            for pattern, repl in self.SUBPHRASE_MAP:
                working = re.sub(pattern, repl, working, flags=re.IGNORECASE)

            # Strip leading/trailing filler words
            working = re.sub(r"\b(mujhe|mujhko|batao|bataiye|samjhaao)\b", "", working, flags=re.IGNORECASE)
            working = re.sub(r"\s+", " ", working).strip()

            return working if working else text, True, "hi-Latn"

        return text, False, "en"
