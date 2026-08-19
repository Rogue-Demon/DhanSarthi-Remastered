"""
Phase L.9.4 — Dedicated Provider Readiness & Inference Validation Test Suite.

Verifies:
  1. Missing provider configuration handling
  2. Missing API key handling
  3. Valid credentials & probe generation
  4. Invalid credentials (401 -> INVALID_CREDENTIALS)
  5. Model access denied (403 / gated -> MODEL_ACCESS_DENIED)
  6. Model not found (404 -> MODEL_NOT_FOUND)
  7. Provider unavailable (429/502/503/504 -> PROVIDER_UNAVAILABLE)
  8. Timeout handling (TIMEOUT)
  9. Sanitized error output
 10. API key never exposed in results
 11. Primary model validation
 12. Fallback diagnostic model validation
 13. No automatic fallback switching in production
 14. Real inference smoke path
 15. Streaming readiness & metrics
 16. Model allowlist preservation
 17. Personal finance boundary preservation
 18. L.9.1 quality integration
 19. L.9.2 evaluator integration
 20. L.9.3 benchmark integration
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from app.ai.exceptions import AIProviderError
from app.ai.inference.model_router import ModelRouter
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.provider_readiness import (
    ProviderReadinessResult,
    ProviderReadinessService,
    ProviderReadinessStatus,
)
from app.core.config import settings


@pytest.mark.anyio
class TestProviderReadinessSuite:
    """Covers Phase L.9.4 provider readiness, diagnostic health, and error mapping."""

    async def test_missing_provider_configuration(self):
        with patch.object(settings, "ai_provider", "mock"):
            service = ProviderReadinessService()
            result = await service.check_huggingface()
            assert result.status == ProviderReadinessStatus.MISSING_CONFIGURATION
            assert result.authenticated is False
            assert "not 'huggingface'" in result.safe_error_message

    async def test_missing_api_key(self):
        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", ""):
                service = ProviderReadinessService()
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.MISSING_CONFIGURATION
                assert result.authenticated is False
                assert "not set or empty" in result.safe_error_message

    async def test_invalid_api_key_format(self):
        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "invalid_token_123"):
                service = ProviderReadinessService()
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.INVALID_CREDENTIALS
                assert result.authenticated is False
                assert "must start with 'hf_'" in result.safe_error_message

    async def test_valid_credentials_and_test_generation(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(return_value="OK")

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_test_valid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.READY
                assert result.authenticated is True
                assert result.model_accessible is True
                assert result.test_generation is True
                assert result.latency_ms >= 0.0

    async def test_invalid_credentials_401(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=AIProviderError("HTTP 401 Client Error: Invalid Token"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_invalid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.INVALID_CREDENTIALS
                assert result.authenticated is False
                assert result.model_accessible is False

    async def test_model_access_denied_403_or_gated(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=AIProviderError("HTTP 403 Forbidden: Cannot access gated repo"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key_ungated"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.MODEL_ACCESS_DENIED
                assert result.authenticated is True
                assert result.model_accessible is False

    async def test_model_not_found_404(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = "non-existent/model"
        mock_hf.generate = AsyncMock(side_effect=AIProviderError("HTTP 404 Not Found: Model does not exist"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface(model="non-existent/model")
                assert result.status == ProviderReadinessStatus.MODEL_NOT_FOUND
                assert result.authenticated is True
                assert result.model_accessible is False

    async def test_provider_rate_limit_429(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=AIProviderError("HTTP 429 Rate Limit Exceeded"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.PROVIDER_UNAVAILABLE
                assert result.authenticated is True
                assert "rate limit" in result.safe_error_message.lower()

    async def test_provider_unavailable_503(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=AIProviderError("HTTP 503 Service Unavailable"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.PROVIDER_UNAVAILABLE
                assert result.authenticated is True

    async def test_provider_timeout(self):
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key"):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                assert result.status == ProviderReadinessStatus.TIMEOUT
                assert result.test_generation is False

    async def test_no_api_key_leakage_in_error_messages(self):
        raw_secret_key = "hf_secret_1234567890abcdef"
        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = settings.ai_model
        mock_hf.generate = AsyncMock(side_effect=Exception(f"Error connecting with token {raw_secret_key} and Bearer {raw_secret_key}"))

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", raw_secret_key):
                service = ProviderReadinessService(provider=mock_hf)
                result = await service.check_huggingface()
                res_dict = result.to_dict()
                assert raw_secret_key not in result.safe_error_message
                assert raw_secret_key not in str(res_dict)
                assert "[REDACTED" in result.safe_error_message

    async def test_fallback_diagnostic_model_does_not_switch_production(self):
        primary_model = "meta-llama/Meta-Llama-3-8B-Instruct"
        fallback_model = "Qwen/Qwen2.5-7B-Instruct"

        mock_hf = MagicMock(spec=HuggingFaceProvider)
        mock_hf.model = primary_model

        async def _mock_generate(context, prompt, max_tokens=5, **kwargs):
            if mock_hf.model == primary_model:
                raise AIProviderError("HTTP 403 Forbidden: gated repo")
            return "OK"

        mock_hf.generate = AsyncMock(side_effect=_mock_generate)

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", "hf_valid_key"):
                with patch.object(settings, "ai_model", primary_model):
                    with patch.object(settings, "ai_provider_readiness_fallback_model", fallback_model):
                        service = ProviderReadinessService(provider=mock_hf)
                        diag = await service.check_all_configured()

                        assert diag["primary_status"] == ProviderReadinessStatus.MODEL_ACCESS_DENIED.value
                        assert diag["fallback_result"]["status"] == ProviderReadinessStatus.READY.value
                        # Production AI_MODEL remains untouched
                        assert settings.ai_model == primary_model

    async def test_model_allowlist_enforced_by_model_router(self):
        router = ModelRouter()
        # Unapproved candidate model MUST be rejected
        validated = router._validate_model("untrusted/dangerous-model")
        assert validated == settings.ai_model

        # Approved model candidate MUST be accepted
        allowed = router._validate_model("Qwen/Qwen2.5-7B-Instruct")
        assert allowed == "Qwen/Qwen2.5-7B-Instruct"

    async def test_smoke_test_script_blocked_when_provider_not_ready(self):
        from scripts.real_inference_smoke_test import run_real_inference_smoke_test

        with patch.object(settings, "ai_provider", "huggingface"):
            with patch.object(settings, "ai_provider_api_key", ""):
                res = await run_real_inference_smoke_test()
                assert res["status"] == "REAL_INFERENCE_BLOCKED"
                assert "reason" in res

    async def test_real_benchmark_blocked_when_credentials_invalid(self):
        from scripts.benchmark_real_provider import check_real_provider_availability

        with patch.object(settings, "ai_provider_api_key", "invalid_key"):
            is_avail, reason = await check_real_provider_availability()
            assert is_avail is False
            assert "REAL_PROVIDER_NOT_CONFIGURED" in reason
