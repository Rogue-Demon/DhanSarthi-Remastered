"""
Phase L.9.4 — Production Provider Readiness & Real Inference Validation Service.

Validates provider credentials, network accessibility, model authorization,
and minimal inference health without leaking sensitive tokens or credentials.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from enum import Enum
import logging
import time
from typing import Any, Dict, Optional

import httpx
from app.ai.exceptions import AIConfigurationError, AIProviderError
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.schemas.advisor import AIContext
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderReadinessStatus(str, Enum):
    """Explicit lifecycle readiness states for the AI provider."""
    READY = "READY"
    MISSING_CONFIGURATION = "MISSING_CONFIGURATION"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    MODEL_ACCESS_DENIED = "MODEL_ACCESS_DENIED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ProviderReadinessResult:
    """Diagnostic readiness report for an AI provider and target model."""
    provider: str
    model: str
    status: ProviderReadinessStatus
    authenticated: bool
    model_accessible: bool
    test_generation: bool
    latency_ms: float
    error_code: Optional[str] = None
    safe_error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return safe, sanitized dictionary guaranteed to contain zero credentials."""
        data = asdict(self)
        data["status"] = self.status.value
        # Strict sanitization check
        for k, v in data.items():
            if isinstance(v, str):
                if "hf_" in v or "Bearer" in v or "sk-" in v:
                    data[k] = "[REDACTED_CREDENTIALS]"
        return data


class ProviderReadinessService:
    """
    Validates end-to-end provider health, authentication, gated model access,
    and minimal test generation execution using existing provider infrastructure.
    """

    def __init__(self, provider: Optional[HuggingFaceProvider] = None) -> None:
        self._provider = provider

    def _sanitize_message(self, message: str) -> str:
        """Remove any inadvertent token/secret substrings from error messages."""
        if not message:
            return ""
        sanitized = message
        if settings.ai_provider_api_key and settings.ai_provider_api_key in sanitized:
            sanitized = sanitized.replace(settings.ai_provider_api_key, "[REDACTED_API_KEY]")
        import re
        sanitized = re.sub(r"hf_[A-Za-z0-9]+", "[REDACTED_TOKEN]", sanitized)
        sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", sanitized)
        return sanitized

    async def check_huggingface(self, model: Optional[str] = None) -> ProviderReadinessResult:
        """
        Check Hugging Face provider readiness for the given model (defaults to settings.ai_model).
        """
        target_model = model or settings.ai_model
        provider_name = settings.ai_provider

        # 1. Verify Configuration Presence
        if provider_name != "huggingface":
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.MISSING_CONFIGURATION,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=0.0,
                error_code="PROVIDER_NOT_HUGGINGFACE",
                safe_error_message=f"AI_PROVIDER is configured as '{provider_name}', not 'huggingface'.",
            )

        api_key = settings.ai_provider_api_key
        if not api_key:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.MISSING_CONFIGURATION,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=0.0,
                error_code="MISSING_API_KEY",
                safe_error_message="AI_PROVIDER_API_KEY is not set or empty.",
            )

        if not api_key.startswith("hf_"):
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.INVALID_CREDENTIALS,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=0.0,
                error_code="INVALID_API_KEY_FORMAT",
                safe_error_message="Hugging Face API key must start with 'hf_'.",
            )

        # 2. Execute Probe Generation via HuggingFaceProvider
        t0 = time.perf_counter()
        try:
            hf = self._provider or HuggingFaceProvider()
            # If a custom model is probed, temporarily set model parameter
            orig_model = hf.model
            if model and model != orig_model:
                hf.model = model

            ctx = AIContext(
                question="readiness_probe",
                user_financial_context=None,
                financial_intelligence=None,
                retrieved_knowledge=[],
                conversation_history=[],
                live_market_data=None,
            )

            # Minimal probe request
            timeout = min(10.0, float(settings.ai_request_timeout_seconds))
            resp = await asyncio.wait_for(
                hf.generate(context=ctx, prompt="Say OK in one word.", max_tokens=5),
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            if model and model != orig_model:
                hf.model = orig_model

            if not resp or len(resp.strip()) == 0:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.UNKNOWN_ERROR,
                    authenticated=True,
                    model_accessible=True,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="EMPTY_GENERATION_RESPONSE",
                    safe_error_message="Provider returned an empty response.",
                )

            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.READY,
                authenticated=True,
                model_accessible=True,
                test_generation=True,
                latency_ms=round(elapsed_ms, 2),
            )

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.TIMEOUT,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="TIMEOUT",
                safe_error_message="Provider connection timed out during readiness probe.",
            )

        except httpx.HTTPStatusError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            code = exc.response.status_code
            return self._classify_http_status_error(code, target_model, provider_name, elapsed_ms, str(exc))

        except AIProviderError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            err_msg = str(exc).lower()
            if "401" in err_msg or "unauthorized" in err_msg:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.INVALID_CREDENTIALS,
                    authenticated=False,
                    model_accessible=False,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_401",
                    safe_error_message="Hugging Face authentication failed. Invalid API token.",
                )
            elif "403" in err_msg or "forbidden" in err_msg or "gated" in err_msg or "restricted" in err_msg:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.MODEL_ACCESS_DENIED,
                    authenticated=True,
                    model_accessible=False,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_403",
                    safe_error_message=f"Model '{target_model}' is gated or access is restricted on Hugging Face.",
                )
            elif "404" in err_msg or "not found" in err_msg:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.MODEL_NOT_FOUND,
                    authenticated=True,
                    model_accessible=False,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_404",
                    safe_error_message=f"Model '{target_model}' was not found on Hugging Face router.",
                )
            elif "429" in err_msg or "rate limit" in err_msg:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.PROVIDER_UNAVAILABLE,
                    authenticated=True,
                    model_accessible=True,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_429",
                    safe_error_message="Hugging Face API rate limit reached.",
                )
            elif any(c in err_msg for c in ["502", "503", "504", "unavailable", "server error"]):
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.PROVIDER_UNAVAILABLE,
                    authenticated=True,
                    model_accessible=True,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_5XX",
                    safe_error_message="Hugging Face service currently unavailable.",
                )
            else:
                return ProviderReadinessResult(
                    provider=provider_name,
                    model=target_model,
                    status=ProviderReadinessStatus.UNKNOWN_ERROR,
                    authenticated=False,
                    model_accessible=False,
                    test_generation=False,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="PROVIDER_ERROR",
                    safe_error_message=self._sanitize_message(str(exc)),
                )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.UNKNOWN_ERROR,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="UNEXPECTED_EXCEPTION",
                safe_error_message=self._sanitize_message(str(exc)),
            )

    def _classify_http_status_error(
        self, code: int, target_model: str, provider_name: str, elapsed_ms: float, raw_err: str
    ) -> ProviderReadinessResult:
        if code == 401:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.INVALID_CREDENTIALS,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="HTTP_401",
                safe_error_message="Hugging Face authentication failed. Invalid API token.",
            )
        elif code == 403:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.MODEL_ACCESS_DENIED,
                authenticated=True,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="HTTP_403",
                safe_error_message=f"Model '{target_model}' is gated or access is restricted.",
            )
        elif code == 404:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.MODEL_NOT_FOUND,
                authenticated=True,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="HTTP_404",
                safe_error_message=f"Model '{target_model}' was not found.",
            )
        elif code == 429:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.PROVIDER_UNAVAILABLE,
                authenticated=True,
                model_accessible=True,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code="HTTP_429",
                safe_error_message="Hugging Face API rate limit reached.",
            )
        elif code in (502, 503, 504):
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.PROVIDER_UNAVAILABLE,
                authenticated=True,
                model_accessible=True,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code=f"HTTP_{code}",
                safe_error_message="Hugging Face inference service temporarily unavailable.",
            )
        else:
            return ProviderReadinessResult(
                provider=provider_name,
                model=target_model,
                status=ProviderReadinessStatus.UNKNOWN_ERROR,
                authenticated=False,
                model_accessible=False,
                test_generation=False,
                latency_ms=round(elapsed_ms, 2),
                error_code=f"HTTP_{code}",
                safe_error_message=self._sanitize_message(raw_err),
            )

    async def check_all_configured(self) -> Dict[str, Any]:
        """
        Check the primary configured model, optional fallback model, and routing tier models.
        Does NOT alter production settings.ai_model.
        """
        primary_result = await self.check_huggingface(settings.ai_model)

        fallback_result = None
        fallback_model = settings.ai_provider_readiness_fallback_model
        if fallback_model and fallback_model != settings.ai_model:
            fallback_result = await self.check_huggingface(fallback_model)

        # Check routing tier models (fast, balanced, reasoning)
        raw_allowed = getattr(settings, "ai_allowed_models", settings.ai_model)
        allowed_set = {m.strip() for m in raw_allowed.split(",") if m.strip()}

        routing_tiers: Dict[str, Any] = {}
        for tier_name, model_attr in [
            ("fast", "ai_fast_model"),
            ("balanced", "ai_balanced_model"),
            ("reasoning", "ai_reasoning_model"),
        ]:
            model_id = getattr(settings, model_attr, settings.ai_model)
            is_allowlisted = model_id in allowed_set
            routing_tiers[tier_name] = {
                "model": model_id,
                "configured": bool(model_id),
                "allowlisted": is_allowlisted,
            }

        return {
            "provider": settings.ai_provider,
            "primary_model": settings.ai_model,
            "primary_status": primary_result.status.value,
            "primary_result": primary_result.to_dict(),
            "fallback_model": fallback_model or None,
            "fallback_result": fallback_result.to_dict() if fallback_result else None,
            "routing_tiers": routing_tiers,
            "overall_status": primary_result.status.value,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
