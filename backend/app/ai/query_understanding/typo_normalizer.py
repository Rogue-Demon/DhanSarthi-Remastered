"""
Financial Typo & Spelling Normalizer for DhanSarthi.

Applies controlled, financial-vocabulary weighted typo correction.
Preserves exact financial acronyms and avoids aggressive generic autocorrection.
"""

from __future__ import annotations

import re
from typing import Tuple


class TypoNormalizer:
    """Financial-vocabulary weighted typo corrector."""

    # Preserved uppercase acronyms
    PRESERVED_ACRONYMS = {
        "SIP", "PPF", "NPS", "SGB", "NAV", "EMI", "TDS", "ITR", "DTI",
        "KYC", "PAN", "IPO", "MF", "FD", "RD", "ASBA", "BSDA", "SCORES",
        "DICGC", "RBI", "SEBI", "PFRDA", "AMFI", "STCG", "LTCG", "HRA",
    }

    # Deterministic financial typo mapping dictionary
    FINANCIAL_TYPO_MAP = {
        "mutal": "mutual",
        "mutal fund": "mutual fund",
        "mutual fnd": "mutual fund",
        "mutuall": "mutual",
        "invesment": "investment",
        "investmant": "investment",
        "invesments": "investments",
        "savngs": "savings",
        "savng": "savings",
        "emergncy": "emergency",
        "emergancy": "emergency",
        "retur": "return",
        "retuns": "returns",
        "divident": "dividend",
        "dividents": "dividends",
        "finacial": "financial",
        "fnancial": "financial",
        "liabilty": "liability",
        "liabilties": "liabilities",
        "expence": "expense",
        "expences": "expenses",
        "retirment": "retirement",
        "retrment": "retirement",
        "portfolo": "portfolio",
        "portfoli": "portfolio",
        "balnce": "balance",
        "amunt": "amount",
        "issurance": "insurance",
        "insuranse": "insurance",
        "interst": "interest",
        "intrst": "interest",
        "ppff": "ppf",
        "sipp": "sip",
        "npss": "nps",
        "mff": "mf",
        "fdd": "fd",
        "wrk": "work",
    }

    def correct(self, text: str) -> Tuple[str, bool, float]:
        """
        Correct obvious financial typos in input text.

        Returns:
            (corrected_text, correction_applied, confidence)
        """
        if not text or not text.strip():
            return text, False, 1.0

        original = text
        working = text
        applied = False
        min_confidence = 1.0

        # Check multi-word phrase corrections first
        working_lower = working.lower()
        for typo_phrase, correct_phrase in self.FINANCIAL_TYPO_MAP.items():
            if " " in typo_phrase and typo_phrase in working_lower:
                pattern = re.compile(re.escape(typo_phrase), re.IGNORECASE)
                working = pattern.sub(correct_phrase, working)
                applied = True
                min_confidence = min(min_confidence, 0.95)

        # Word-by-word token correction
        words = working.split()
        corrected_words = []

        for word in words:
            # Preserve punctuation on word boundaries
            prefix = ""
            suffix = ""
            match = re.match(r"^([^\w]*)(.*?)([^\w]*)$", word)
            if match:
                prefix, core, suffix = match.groups()
            else:
                core = word

            core_upper = core.upper()

            # Preserve exact financial acronyms
            if core_upper in self.PRESERVED_ACRONYMS:
                corrected_words.append(prefix + core_upper + suffix)
                continue

            core_lower = core.lower()
            if core_lower in self.FINANCIAL_TYPO_MAP:
                corrected_words.append(prefix + self.FINANCIAL_TYPO_MAP[core_lower] + suffix)
                applied = True
                min_confidence = min(min_confidence, 0.92)
            else:
                corrected_words.append(word)

        result_text = " ".join(corrected_words)

        # Fix spacing around punctuation
        result_text = re.sub(r"\s+([?!.,])", r"\1", result_text)

        return result_text, applied, min_confidence if applied else 1.0
