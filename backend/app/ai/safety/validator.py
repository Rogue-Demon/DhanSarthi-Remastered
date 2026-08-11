"""
Extended safety validator with system prompt leakage detection and enhanced checks.
"""

from __future__ import annotations

import re
from app.ai.exceptions import AISafetyError
from app.ai.safety.base import AISafetyValidator
from app.ai.schemas.advisor import AIContext


class SimpleSafetyValidator(AISafetyValidator):
    """Enforces boundaries: prevents secrets leaks, prompt injection, autonomous transaction claims."""

    def __init__(self) -> None:
        # Regex patterns to detect high-risk inputs/outputs
        self._secret_patterns = [
            re.compile(r"ey[a-zA-Z0-9-_=]+\.ey[a-zA-Z0-9-_=]+\.[a-zA-Z0-9-_=]+"),  # JWT pattern
            re.compile(r"\b[0-9a-fA-F]{32,64}\b"),                                   # MD5/SHA hex hashes
            re.compile(r"\b(api_key|password_hash|secret|auth_token)\s*[:=]\s*\S+", re.IGNORECASE),
        ]

        # Phrases that indicate system prompt leakage
        self._system_prompt_leak_phrases = [
            "system instructions:",
            "you are dhansarthi,",
            "do not execute numerical",
            "user financial facts (authenticated",
        ]

        # Phrase patterns to block autonomous execution claims
        self._action_patterns = [
            re.compile(
                r"\b(initiated|executing|transferring|buying|selling|transferred|"
                r"bought|sold|submitted|approved)\b.*\b(on your behalf|money|funds|stocks|shares|loan)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(i have transferred|i have bought|i have sold|i have applied for|i have submitted the tax)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(execute transfer|initiate payment|place (the |a )?trade|submit (the |a )?loan application)\b",
                re.IGNORECASE,
            ),
        ]

    def validate_response(self, response: str, context: AIContext) -> None:
        """
        Scan response text and raise AISafetyError if any rules are violated.

        Rules enforced:
          1. No secret/credential patterns.
          2. No system prompt content verbatim.
          3. No autonomous financial action claims.
          4. No unsafe guarantees about returns or approvals.
          5. Response must not be empty.
        """
        # Rule 0: Non-empty
        if not response or not response.strip():
            raise AISafetyError("LLM returned an empty response.")

        # Rule 1: No secrets
        for pattern in self._secret_patterns:
            if pattern.search(response):
                raise AISafetyError("Response contains patterns resembling API keys, passwords, or tokens.")

        # Rule 2: No system prompt leakage
        lower_resp = response.lower()
        for phrase in self._system_prompt_leak_phrases:
            if phrase in lower_resp:
                raise AISafetyError(
                    f"Response appears to expose internal system instructions. "
                    f"Detected phrase: '{phrase}'"
                )

        # Rule 3: No autonomous action execution claims
        for pattern in self._action_patterns:
            if pattern.search(response):
                raise AISafetyError(
                    "Response attempts to execute or claim autonomous financial transactions."
                )

        # Rule 4: No unsafe guarantees on returns or approvals
        if "guarantee" in lower_resp and any(
            word in lower_resp
            for word in ["return", "growth", "interest", "profit", "approval", "approve"]
        ):
            raise AISafetyError(
                "Response makes unsafe guarantees about investment returns or loan approvals."
            )
