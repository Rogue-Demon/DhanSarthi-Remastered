"""
Provider Failure Classifier and Model Fallback Coordinator for Phase L.9.9.

Classifies upstream provider exceptions into typed ResilienceFailureType categories,
sanitizes error strings to prevent token/key leakage, and orchestrates model fallback
using the server-configured allowlist from L.8 ModelRouter.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, List, Optional, Set, Union

from fastapi import HTTPException
import httpx

from app.ai.exceptions import AIConfigurationError, AIProviderError
from app.ai.schemas.resilience import FallbackType, ResilienceFailureType
from app.core.config import settings

logger = logging.getLogger(__name__)

# Patterns for scrubbing credentials / secrets from exception messages
_SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{8,}", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{8,}['\"]?", re.IGNORECASE),
    re.compile(r"hf_[A-Za-z0-9]{10,}", re.IGNORECASE),
]


def classify_provider_failure(exc: Exception) -> ResilienceFailureType:
    """
    Deterministically map an exception to a ResilienceFailureType.

    Rules:
      - asyncio.CancelledError -> CLIENT_CANCELLED
      - 401 / "Invalid API key" -> AUTHENTICATION
      - 403 / "Unauthorized" -> AUTHORIZATION
      - 429 / "rate limit" -> RATE_LIMIT
      - 502 / 503 / "Service Unavailable" -> PROVIDER_UNAVAILABLE
      - 504 / "Gateway Timeout" -> PROVIDER_TIMEOUT
      - asyncio.TimeoutError / TimeoutError -> PROVIDER_TIMEOUT
      - httpx.TimeoutException -> NETWORK_TIMEOUT
      - Malformed payload / parsing error -> MALFORMED_PROVIDER_RESPONSE
    """
    if isinstance(exc, asyncio.CancelledError):
        return ResilienceFailureType.CLIENT_CANCELLED

    if isinstance(exc, HTTPException):
        if exc.status_code == 401:
            return ResilienceFailureType.AUTHENTICATION
        if exc.status_code == 403:
            return ResilienceFailureType.AUTHORIZATION
        if exc.status_code == 429:
            return ResilienceFailureType.RATE_LIMIT
        if exc.status_code in (502, 503):
            return ResilienceFailureType.PROVIDER_UNAVAILABLE
        if exc.status_code == 504:
            return ResilienceFailureType.PROVIDER_TIMEOUT

    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.TimeoutException)):
        return ResilienceFailureType.NETWORK_TIMEOUT

    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return ResilienceFailureType.PROVIDER_TIMEOUT

    exc_str = str(exc).lower()

    if "401" in exc_str or "unauthorized" in exc_str or "invalid api key" in exc_str or "gated repo" in exc_str:
        return ResilienceFailureType.AUTHENTICATION

    if "403" in exc_str or "forbidden" in exc_str or "permission denied" in exc_str:
        return ResilienceFailureType.AUTHORIZATION

    if "429" in exc_str or "rate limit" in exc_str or "too many requests" in exc_str:
        return ResilienceFailureType.RATE_LIMIT

    if "504" in exc_str or "gateway timeout" in exc_str or "timeout" in exc_str or "timed out" in exc_str:
        return ResilienceFailureType.PROVIDER_TIMEOUT

    if "502" in exc_str or "503" in exc_str or "bad gateway" in exc_str or "service unavailable" in exc_str or "loading" in exc_str:
        return ResilienceFailureType.PROVIDER_UNAVAILABLE

    if "json" in exc_str or "malformed" in exc_str or "decode" in exc_str or "parse" in exc_str:
        return ResilienceFailureType.MALFORMED_PROVIDER_RESPONSE

    return ResilienceFailureType.UNKNOWN


def sanitize_error_message(exc: Union[Exception, str]) -> str:
    """
    Scrub raw exception messages to ensure no credentials, tokens, or internal secrets leak.
    """
    raw = str(exc)
    sanitized = raw
    for pat in _SECRET_PATTERNS:
        sanitized = pat.sub("[REDACTED]", sanitized)
    return sanitized


class ModelFallbackCoordinator:
    """
    Coordinates model candidate fallback upon transient provider failure.
    
    Adheres strictly to the server-configured AI_ALLOWED_MODELS allowlist.
    Hierarchy:
      Current Selected Model -> Allowed Balanced Model -> Allowed Fast Model -> None
    """

    def __init__(self, allowed_models: Optional[List[str]] = None) -> None:
        self.enabled = getattr(settings, "ai_provider_fallback_enabled", True)
        self.fast_model = getattr(settings, "ai_fast_model", settings.ai_model)
        self.balanced_model = getattr(settings, "ai_balanced_model", settings.ai_model)
        self.primary_model = settings.ai_model

        if allowed_models is not None:
            self.allowed_models: Set[str] = set(allowed_models)
        else:
            raw_allowed = getattr(settings, "ai_allowed_models", settings.ai_model)
            self.allowed_models = {m.strip() for m in raw_allowed.split(",") if m.strip()}
            self.allowed_models.add(self.primary_model)

    def get_fallback_model(self, current_model: str, attempted_models: Optional[Set[str]] = None) -> Optional[str]:
        """
        Determine the next model candidate from the server allowlist.

        Returns:
            Model identifier string or None if fallback candidates are exhausted.
        """
        if not self.enabled:
            return None

        tried = set(attempted_models) if attempted_models else set()
        tried.add(current_model)

        # Fallback candidate order: balanced -> fast -> primary -> any remaining allowed model
        candidates = [self.balanced_model, self.fast_model, self.primary_model]
        for m in self.allowed_models:
            if m not in candidates:
                candidates.append(m)

        for cand in candidates:
            if cand in self.allowed_models and cand not in tried:
                logger.info(f"ModelFallbackCoordinator selecting alternative model: {cand} (was: {current_model})")
                return cand

        return None
