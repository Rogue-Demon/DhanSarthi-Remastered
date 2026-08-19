"""
Conversation Reference & Pronoun Resolver for DhanSarthi.

Resolves conversational pronouns and ambiguous references ("it", "this", "that",
"this fund", "this investment") against recent dialogue history.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.ai.schemas.query_understanding import ConversationReference


class ReferenceResolver:
    """Resolves conversational references using recent dialogue history."""

    PRONOUN_PATTERNS = [
        (r"\b(is\s+it|it\s+is|about\s+it|in\s+it|for\s+it)\b", "it"),
        (r"\b(this\s+investment|this\s+fund|this\s+scheme|this\s+one|this)\b", "this"),
        (r"\b(that\s+investment|that\s+fund|that\s+scheme|that)\b", "that"),
        (r"\b(the\s+above|same)\b", "the above"),
    ]

    # Domain topic keywords to scan for in previous dialogue
    DOMAIN_TOPICS = [
        "Systematic Investment Plan", "SIP",
        "Mutual Funds", "Mutual Fund", "MF",
        "Public Provident Fund", "PPF",
        "National Pension System", "NPS",
        "Fixed Deposit", "FD",
        "Recurring Deposit", "RD",
        "Sovereign Gold Bond", "SGB",
        "Equated Monthly Installment", "EMI",
        "Net Asset Value", "NAV",
        "Emergency Fund", "Debt-to-Income", "DTI",
    ]

    def resolve(
        self, query: str, history: Optional[List] = None
    ) -> Tuple[str, Optional[ConversationReference]]:
        """
        Resolve pronouns/references in query using dialogue history.

        Returns:
            (resolved_query, conversation_reference)
        """
        if not query or not history:
            return query, None

        q_lower = query.lower().strip()

        # Check if query contains conversational references
        detected_pronoun = None
        for pattern, pronoun_name in self.PRONOUN_PATTERNS:
            if re.search(pattern, q_lower):
                detected_pronoun = pronoun_name
                break

        if not detected_pronoun:
            # Special check: short ambiguous follow-ups like "is it safe?", "how much should I invest?"
            if q_lower in {"is it safe?", "is it safe", "is it risky?", "is it risky", "how much should i invest?", "how to start?"}:
                detected_pronoun = "it"

        if not detected_pronoun:
            return query, None

        # Scan previous messages (newest first) for domain topic
        target_topic = None
        for msg in reversed(history):
            content = getattr(msg, "content", "") if not isinstance(msg, dict) else msg.get("content", "")
            if not content:
                continue

            # Look for explicit topics in previous message content
            for topic in self.DOMAIN_TOPICS:
                if re.search(r"\b" + re.escape(topic) + r"\b", content, re.IGNORECASE):
                    target_topic = topic
                    break
            if target_topic:
                break

        if not target_topic:
            # Ambiguous reference cannot be resolved confidently
            return query, ConversationReference(
                pronoun=detected_pronoun,
                resolved_target="UNKNOWN",
                confidence=0.0,
            )

        # Substitute pronoun with resolved topic string
        resolved = query
        if detected_pronoun in ("it", "this", "that"):
            # Replace "it", "this", "that" when used as pronoun
            resolved = re.sub(r"\b(it|this|that)\b", target_topic, query, flags=re.IGNORECASE)
        elif detected_pronoun in ("this investment", "this fund", "this scheme", "this one"):
            resolved = re.sub(
                r"\b(this investment|this fund|this scheme|this one)\b",
                target_topic,
                query,
                flags=re.IGNORECASE,
            )

        ref = ConversationReference(
            pronoun=detected_pronoun,
            resolved_target=target_topic,
            confidence=0.95,
        )

        return resolved, ref
