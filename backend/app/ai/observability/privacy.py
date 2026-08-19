"""
Privacy & Telemetry Sanitization Subsystem for DhanSarthi Phase L.10.

Ensures no raw prompts, user queries, credentials, Bearer tokens, API keys,
PII (emails, phone numbers), or personal financial amounts can leak into stored telemetry.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

# Regex patterns for credentials, tokens, and sensitive headers
_BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{10,}", re.IGNORECASE)
_API_KEY_PATTERN = re.compile(r"(?:api[_-]?key|access[_-]?token|secret|token|password)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.]{8,})[\"']?", re.IGNORECASE)
_HF_TOKEN_PATTERN = re.compile(r"hf_[A-Za-z0-9]{20,}")
_AUTH_HEADER_PATTERN = re.compile(r"Authorization:\s*[^\r\n]+", re.IGNORECASE)
_URL_TOKEN_PATTERN = re.compile(r"([?&](?:api_key|token|access_token|key|secret)=)[^&\s]+", re.IGNORECASE)

# PII Patterns
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")

# Financial Currency / Amount Patterns in text
_FINANCIAL_AMOUNT_PATTERN = re.compile(r"(?:₹|Rs\.?|INR|\$)\s*[\d,]+(?:\.\d+)?|\b\d{5,}\b")

_SALT = "DhanSarthi_Telemetry_Salt_2026"


def hash_identifier(identifier: Optional[Any]) -> Optional[str]:
    """
    Produce a deterministic one-way SHA-256 hash of an identifier (e.g., conversation_id).
    Never reversible to the original user or entity identity.
    """
    if identifier is None:
        return None
    raw_str = f"{_SALT}:{identifier}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def sanitize_text_field(text: Optional[str]) -> str:
    """
    Scrub all credentials, tokens, emails, phone numbers, and raw numbers from a string.
    """
    if not text or not isinstance(text, str):
        return ""

    sanitized = _AUTH_HEADER_PATTERN.sub("Authorization: [REDACTED]", text)
    sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", sanitized)
    sanitized = _HF_TOKEN_PATTERN.sub("[REDACTED_HF_TOKEN]", sanitized)
    sanitized = _URL_TOKEN_PATTERN.sub(r"\1[REDACTED]", sanitized)
    sanitized = _API_KEY_PATTERN.sub("api_key=[REDACTED]", sanitized)
    sanitized = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)
    sanitized = _PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)
    sanitized = _FINANCIAL_AMOUNT_PATTERN.sub("[REDACTED_AMOUNT]", sanitized)

    return sanitized


def sanitize_metadata_dict(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Recursively sanitize metadata dictionary to ensure only safe primitive keys/values remain.
    Discards raw query, prompt, response, or personal financial payload keys.
    """
    if not metadata or not isinstance(metadata, dict):
        return {}

    banned_keys = {
        "prompt", "raw_prompt", "response", "raw_response", "query", "user_query",
        "message", "content", "personal_context", "financial_context", "user_financial_context",
        "full_context", "auth", "authorization", "api_key", "password", "token",
        "hf_token", "secret", "user_id", "email", "phone"
    }

    clean: Dict[str, Any] = {}
    for k, v in metadata.items():
        k_lower = str(k).lower()
        if k_lower in banned_keys:
            continue
        if isinstance(v, (int, float, bool)):
            clean[k] = v
        elif isinstance(v, str):
            clean[k] = sanitize_text_field(v)
        elif isinstance(v, dict):
            clean[k] = sanitize_metadata_dict(v)
        elif isinstance(v, list):
            clean_list: List[Any] = []
            for item in v:
                if isinstance(item, (int, float, bool)):
                    clean_list.append(item)
                elif isinstance(item, str):
                    clean_list.append(sanitize_text_field(item))
                elif isinstance(item, dict):
                    clean_list.append(sanitize_metadata_dict(item))
            clean[k] = clean_list

    return clean
