"""
Hugging Face model provider implementing the LLMProvider and EmbeddingProvider interfaces.

Phase L.7.3 changes (builds on L.7.2):
- Connection pool parameters now read from Settings (AI_HTTP_MAX_CONNECTIONS, etc.).
- Retry policy with exponential backoff + jitter (AI_MAX_RETRIES, default 1).
  Retryable: httpx.RequestError, HTTP 502, 503 (loading), 504.
  NOT retried: 400, 401, 403, 429, AIConfigurationError.
- aclose(): gracefully closes the persistent AsyncClient (called by FastAPI lifespan).
- embed(): uses shared persistent _client (eliminates per-embed TCP setup).
- generate_stream(): SSE streaming implementation for AI_STREAMING_ENABLED=true.
  Streams preview chunks to caller; full assembled text still passes SafetyValidator.
- Retry count, request_status, provider_name, streaming_used recorded in tracker.
- TTFB/TTFT formally documented as STREAMING_NOT_SUPPORTED (non-streaming mode).
- No credentials, no prompt text, no personal numbers logged at any level.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, AsyncIterator, Optional

import httpx

from app.ai.exceptions import AIConfigurationError, AIProviderError
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.schemas.advisor import AIContext
from app.core.config import settings

logger = logging.getLogger(__name__)

# Approximate characters-per-token ratio for quick token count estimation.
# LLaMA tokenizer averages ~3.8–4.2 chars/token for English financial text.
_CHARS_PER_TOKEN_ESTIMATE: float = 4.0

# HTTP status codes that indicate a transient server-side failure worth retrying.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({502, 503, 504})

# HTTP status codes that are definitively non-retryable (auth / rate-limit / bad request).
_NON_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({400, 401, 403, 429})

# Maximum per-attempt backoff cap (seconds)
_MAX_BACKOFF_SECONDS: float = 10.0

# Base backoff multiplier
_BACKOFF_BASE: float = 0.5


class HuggingFaceProvider(LLMProvider, EmbeddingProvider):
    """Integrates with Hugging Face Inference API for text generation and embeddings.

    Phase L.7.3:
      - A single persistent AsyncClient is shared across ALL calls within the provider
        instance lifetime (eliminates repeated TCP connection overhead).
      - Connection pool size configurable via Settings (AI_HTTP_MAX_CONNECTIONS et al.).
      - Transient failures retried up to AI_MAX_RETRIES times with exponential backoff.
      - aclose() must be called at application shutdown (registered in FastAPI lifespan).
    """

    def __init__(self) -> None:
        self.api_key = settings.ai_provider_api_key
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        self.temperature = settings.ai_temperature

        if not self.api_key or not self.api_key.strip():
            raise AIConfigurationError(
                "Hugging Face API Key is not configured. Set AI_PROVIDER_API_KEY environment variable."
            )

        self.endpoint = "https://router.huggingface.co/v1/chat/completions"

        # --- Phase L.7.3: Connection pool config from Settings ---
        timeout = float(settings.ai_request_timeout_seconds)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            http2=False,
            limits=httpx.Limits(
                max_keepalive_connections=settings.ai_http_max_keepalive_connections,
                max_connections=settings.ai_http_max_connections,
                keepalive_expiry=settings.ai_http_keepalive_seconds,
            ),
        )

    # ------------------------------------------------------------------
    # LLMProvider interface — standard (non-streaming)
    # ------------------------------------------------------------------

    async def generate(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Query Hugging Face Router API for text generation (non-streaming).

        Implements retry with exponential backoff + jitter for transient failures.
        TTFB / TTFT are formally logged as None (STREAMING_NOT_SUPPORTED: without SSE
        streaming httpx cannot split header arrival from body transfer time).

        Args:
            context: Structured AIContext container (user facts + RAG knowledge).
            prompt: Final assembled system/user prompt string.
            tracker: Optional LatencyTracker for observability recording.
            max_tokens: Per-request token budget override from TokenBudgetSelector.

        Returns:
            str: Raw LLM response string.

        Raises:
            AIProviderError: When the underlying API call fails after all retries.
            AIConfigurationError: When credentials are invalid (never retried).
        """
        if tracker:
            tracker.record_str("provider_name", "huggingface")
            tracker.record_flag("streaming_used", False)

        config = kwargs.get("config") or kwargs.get("inference_config")
        routing_decision = kwargs.get("routing_decision")
        override_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else None)

        if config:
            effective_max_tokens = config.max_tokens
            effective_temperature = getattr(config, "temperature", self.temperature)
        else:
            effective_max_tokens = max_tokens if (max_tokens is not None and max_tokens > 0) else self.max_tokens
            effective_temperature = self.temperature

        effective_max_tokens = min(effective_max_tokens, settings.ai_max_tokens_global_safety_max)

        target_model = override_model or self.model
        model_name = self._resolve_model_name(target_model)

        from app.ai.inference.tokenizer import get_tokenizer
        tokenizer = get_tokenizer()

        t_tok_start = time.perf_counter()
        prompt_tokens = tokenizer.count_tokens(prompt)
        tok_count_ms = (time.perf_counter() - t_tok_start) * 1000.0

        if tracker:
            tracker.record_count("max_tokens_budget", effective_max_tokens)
            tracker.record_count("effective_max_tokens", effective_max_tokens)
            tracker.record_str("model_name", model_name)
            tracker.record_str("selected_model", model_name)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)
            tracker.record_count("prompt_tokens", prompt_tokens)
            tracker.record_count("prompt_token_count", prompt_tokens)
            tracker.record("tokenizer_count_ms", tok_count_ms)

        max_retries = max(0, settings.ai_max_retries)
        last_exc: Optional[Exception] = None

        # --- Retry loop ---
        for attempt in range(max_retries + 1):
            if attempt > 0:
                backoff = min(_BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.2), _MAX_BACKOFF_SECONDS)
                logger.debug("HF provider retry attempt=%d, backoff=%.2fs", attempt, backoff)
                await asyncio.sleep(backoff)
                if tracker:
                    tracker.increment_count("retry_count")

            try:
                t_gen_start = time.perf_counter()
                result = await self._do_generate(prompt, model_name, effective_max_tokens, tracker, temperature=effective_temperature)
                gen_ms = (time.perf_counter() - t_gen_start) * 1000.0

                t_resp_tok_start = time.perf_counter()
                generated_tokens = tokenizer.count_tokens(result)
                resp_tok_count_ms = (time.perf_counter() - t_resp_tok_start) * 1000.0

                if tracker:
                    status = "RETRY_SUCCESS" if attempt > 0 else "SUCCESS"
                    tracker.record_str("request_status", status)
                    tracker.record_count("generated_tokens", generated_tokens)
                    tracker.record_count("response_token_count", generated_tokens)
                    tracker.increment_count("tokenizer_count_ms", resp_tok_count_ms)
                    gen_sec = (gen_ms / 1000.0) if gen_ms > 0 else 0.001
                    tps = round(generated_tokens / gen_sec, 2) if generated_tokens > 0 else 0.0
                    tracker.record("tokens_per_second", tps)

                return result

            except AIConfigurationError:
                # Never retry auth / config errors
                if tracker:
                    tracker.record_str("request_status", "FAILED")
                raise

            except AIProviderError as exc:
                # Check if this status is worth retrying
                status_code = getattr(exc, "_status_code", None)
                if status_code is not None and status_code in _NON_RETRYABLE_STATUS_CODES:
                    if tracker:
                        tracker.record_str("request_status", "FAILED")
                    raise

                last_exc = exc
                if attempt >= max_retries:
                    # Final attempt failed
                    if tracker:
                        tracker.record_str("request_status", "FAILED")
                    raise

            except httpx.RequestError as exc:
                last_exc = exc
                if attempt >= max_retries:
                    if tracker:
                        tracker.record_str("request_status", "FAILED")
                    raise AIProviderError(f"HTTP request to Hugging Face failed: {str(exc)}") from exc

        # Should never reach here
        if tracker:
            tracker.record_str("request_status", "FAILED")
        raise AIProviderError(f"Hugging Face provider failed after {max_retries + 1} attempt(s): {last_exc}")

    # ------------------------------------------------------------------
    # LLMProvider interface — SSE streaming (Phase L.7.3 / L.8)
    # ------------------------------------------------------------------

    async def generate_stream(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream text generation via SSE (AI_STREAMING_ENABLED=true path).

        Instruments TTFT (Time To First Token) and real token generation metrics.
        """
        if tracker:
            tracker.record_str("provider_name", "huggingface")
            tracker.record_flag("streaming_used", True)

        config = kwargs.get("config") or kwargs.get("inference_config")
        routing_decision = kwargs.get("routing_decision")
        override_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else None)

        if config:
            effective_max_tokens = config.max_tokens
            effective_temperature = getattr(config, "temperature", self.temperature)
        else:
            effective_max_tokens = max_tokens if (max_tokens is not None and max_tokens > 0) else self.max_tokens
            effective_temperature = self.temperature

        effective_max_tokens = min(effective_max_tokens, settings.ai_max_tokens_global_safety_max)

        target_model = override_model or self.model
        model_name = self._resolve_model_name(target_model)

        from app.ai.inference.tokenizer import get_tokenizer
        tokenizer = get_tokenizer()

        t_tok_start = time.perf_counter()
        prompt_tokens = tokenizer.count_tokens(prompt)
        tok_count_ms = (time.perf_counter() - t_tok_start) * 1000.0

        if tracker:
            tracker.record_count("max_tokens_budget", effective_max_tokens)
            tracker.record_count("effective_max_tokens", effective_max_tokens)
            tracker.record_str("model_name", model_name)
            tracker.record_str("selected_model", model_name)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)
            tracker.record_count("prompt_tokens", prompt_tokens)
            tracker.record_count("prompt_token_count", prompt_tokens)
            tracker.record("tokenizer_count_ms", tok_count_ms)

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": effective_max_tokens,
            "temperature": effective_temperature,
            "stream": True,
        }

        start_stream = time.perf_counter()
        first_chunk_received = False
        first_chunk_ttft: Optional[float] = None
        total_chunks = 0
        full_text_parts: list[str] = []

        if tracker:
            tracker.record("request_start_ms", round(time.time() * 1000.0, 2))

        try:
            async with self._client.stream("POST", self.endpoint, json=payload) as response:
                if response.status_code == 401:
                    raise AIConfigurationError("Invalid Hugging Face API key credentials.")
                if response.status_code == 429:
                    raise AIProviderError("Hugging Face API rate limit reached (HTTP 429). Please retry shortly.")
                if response.status_code in _NON_RETRYABLE_STATUS_CODES:
                    exc = AIProviderError(f"Hugging Face streaming rejected with status {response.status_code}")
                    exc._status_code = response.status_code  # type: ignore[attr-defined]
                    raise exc
                if response.status_code not in (200,):
                    raise AIProviderError(
                        f"Hugging Face streaming returned status {response.status_code}"
                    )

                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line or not line.startswith("data:"):
                        continue

                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        import json
                        chunk_data = json.loads(data_str)
                        delta = (
                            chunk_data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if delta:
                            if not first_chunk_received:
                                # Record True TTFT (time to first token chunk)
                                ttft_ms = (time.perf_counter() - start_stream) * 1000.0
                                first_chunk_ttft = ttft_ms
                                if tracker:
                                    tracker.record("ttft_ms", round(ttft_ms, 2))
                                    tracker.record("time_to_first_byte_ms", round(ttft_ms, 2))
                                    tracker.record("time_to_first_token_ms", round(ttft_ms, 2))
                                first_chunk_received = True
                            full_text_parts.append(delta)
                            total_chunks += 1
                            yield delta

                    except Exception:
                        # Skip malformed SSE chunk
                        continue

        except asyncio.CancelledError:
            if tracker:
                tracker.record_str("request_status", "CANCELLED")
            logger.debug("Hugging Face provider stream cancelled by client/task.")
            raise
        except (AIConfigurationError, AIProviderError):
            if tracker:
                tracker.record_str("request_status", "FAILED")
            raise
        except httpx.TimeoutException as exc:
            if tracker:
                tracker.record_str("request_status", "TIMEOUT")
            raise AIProviderError(f"Hugging Face stream timed out after {settings.ai_request_timeout_seconds}s.") from exc
        except httpx.RequestError as exc:
            if tracker:
                tracker.record_str("request_status", "FAILED")
            raise AIProviderError(f"SSE stream connection to Hugging Face failed: {str(exc)}") from exc

        # Record total stream time and assembled response length
        stream_total_ms = (time.perf_counter() - start_stream) * 1000.0
        assembled = "".join(full_text_parts)
        t_resp_tok_start = time.perf_counter()
        generated_tokens = tokenizer.count_tokens(assembled)
        resp_tok_count_ms = (time.perf_counter() - t_resp_tok_start) * 1000.0

        if tracker:
            tracker.record("total_llm_ms", stream_total_ms)
            tracker.record("llm_request_ms", stream_total_ms)
            gen_ms = max(0.0, stream_total_ms - (first_chunk_ttft or 0.0))
            tracker.record("generation_ms", gen_ms)
            tracker.record("llm_generation_ms", stream_total_ms)
            tracker.record_count("generated_tokens", generated_tokens)
            tracker.record_count("response_token_count", generated_tokens)
            tracker.increment_count("tokenizer_count_ms", resp_tok_count_ms)
            gen_sec = (stream_total_ms / 1000.0) if stream_total_ms > 0 else 0.001
            tps = round(generated_tokens / gen_sec, 2) if generated_tokens > 0 else 0.0
            tracker.record("tokens_per_second", tps)
            tracker.record_str("request_status", "SUCCESS")

    # ------------------------------------------------------------------
    # EmbeddingProvider interface
    # ------------------------------------------------------------------

    async def embed(self, text: str) -> list[float]:
        """
        Query Hugging Face Feature Extraction model for vector embeddings.

        Phase L.7.3: Uses shared persistent _client (eliminates per-embed TCP setup).
        Falls back to a deterministic vector if embedding endpoint is unavailable.
        """
        dim = settings.embedding_dimension or 384
        embedding_model = settings.embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
        endpoint = f"https://router.huggingface.co/hf-inference/models/{embedding_model}"
        payload = {"inputs": text}

        try:
            response = await self._client.post(endpoint, json=payload)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], float):
                    return [float(x) for x in data]
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    return [float(x) for x in data[0]]
        except Exception:
            pass

        # Deterministic fallback vector matching dimension
        base = [0.1 * ((i % 10) + 1) for i in range(dim)]
        if text:
            mod = (sum(ord(c) for c in text) % 10) * 0.01
            base = [x + mod for x in base]
        return base

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """
        Gracefully close the persistent HTTP client.

        Called by the FastAPI lifespan shutdown hook to ensure all TCP connections
        are cleanly terminated (avoids socket leak warnings in uvicorn).
        """
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("HuggingFaceProvider: persistent HTTP client closed.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _do_generate(
        self,
        prompt: str,
        model_name: str,
        effective_max_tokens: int,
        tracker: Optional[Any],
        temperature: Optional[float] = None,
    ) -> str:
        """
        Single (non-retried) generation attempt.

        TTFB / TTFT are NOT available in non-streaming mode:
        httpx.AsyncClient cannot separate TCP header arrival from body transfer
        without SSE streaming. Logged formally as None.
        STREAMING_NOT_SUPPORTED: TTFB/TTFT unavailable in non-streaming generate().
        """
        temp = temperature if temperature is not None else self.temperature
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": effective_max_tokens,
            "temperature": temp,
        }

        start_llm = time.perf_counter() if tracker else 0.0

        response = await self._client.post(self.endpoint, json=payload)

        # Fallback to model-specific endpoint if router returns model_not_supported (400)
        if response.status_code == 400:
            fallback_endpoint = (
                f"https://router.huggingface.co/hf-inference/models/{self.model}"
            )
            fallback_payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": effective_max_tokens,
                    "temperature": self.temperature,
                    "return_full_text": False,
                },
            }
            response = await self._client.post(fallback_endpoint, json=fallback_payload)

        # Record round-trip time
        if tracker and start_llm > 0.0:
            llm_total_ms = (time.perf_counter() - start_llm) * 1000.0
            tracker.record("llm_request_ms", llm_total_ms)
            # llm_generation_ms = llm_request_ms for non-streaming (body is always complete).
            tracker.record("llm_generation_ms", llm_total_ms)
            # STREAMING_NOT_SUPPORTED: TTFB/TTFT unavailable without SSE streaming.
            # time_to_first_byte_ms and time_to_first_token_ms remain None.

        # --- Status handling ---
        if response.status_code == 401:
            raise AIConfigurationError("Invalid Hugging Face API key credentials.")
        if response.status_code == 429:
            exc = AIProviderError("Hugging Face API rate limit exceeded. Please try again later.")
            exc._status_code = 429  # type: ignore[attr-defined]
            raise exc
        if response.status_code in _RETRYABLE_STATUS_CODES:
            data = {}
            try:
                ct = response.headers.get("content-type", "")
                if "application/json" in ct:
                    data = response.json()
            except Exception:
                pass
            err_msg = data.get("error", f"Provider returned status {response.status_code}")
            exc = AIProviderError(f"Hugging Face transient error ({response.status_code}): {err_msg}")
            exc._status_code = response.status_code  # type: ignore[attr-defined]
            raise exc
        if response.status_code != 200:
            exc = AIProviderError(
                f"Hugging Face API returned error status {response.status_code}"
            )
            exc._status_code = response.status_code  # type: ignore[attr-defined]
            raise exc

        # --- Parse response ---
        start_parse = time.perf_counter() if tracker else 0.0
        data = response.json()
        res_text = self._extract_response_text(data)

        if tracker and start_parse > 0.0:
            parse_ms = (time.perf_counter() - start_parse) * 1000.0
            tracker.record("llm_response_parse_ms", parse_ms)
            if res_text is not None:
                estimated_resp_tokens = int(len(res_text) / _CHARS_PER_TOKEN_ESTIMATE)
                tracker.record_count("response_token_count", estimated_resp_tokens)

        if res_text is not None:
            return res_text

        raise AIProviderError(f"Unexpected response format from Hugging Face: {str(type(data))}")

    @staticmethod
    def _resolve_model_name(model: str) -> str:
        """
        Normalize model name for HF Router compatibility.

        HF Router does not currently support all model aliases.
        """
        alias_map = {
            "meta-llama/Meta-Llama-3-8B-Instruct": "meta-llama/Llama-3.1-8B-Instruct",
        }
        return alias_map.get(model, model)

    @staticmethod
    def _extract_response_text(data: Any) -> Optional[str]:
        """
        Extract the generated text string from the Hugging Face API response payload.

        Handles:
          - OpenAI-compatible chat completions: data["choices"][0]["message"]["content"]
          - Alternative chat format: data["choices"][0]["text"]
          - Legacy text generation: data["generated_text"]
          - Batch list format: data[0]["generated_text"]  (str or list-of-messages)
          - Summarization: data[0]["summary_text"]
        """
        if isinstance(data, dict):
            if "choices" in data and len(data["choices"]) > 0 and isinstance(data["choices"][0], dict):
                choice = data["choices"][0]
                if "message" in choice and isinstance(choice["message"], dict) and "content" in choice["message"]:
                    return str(choice["message"]["content"]).strip()
                elif "text" in choice:
                    return str(choice["text"]).strip()
            elif "generated_text" in data:
                return str(data["generated_text"]).strip()
        elif isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                if "generated_text" in first:
                    gen = first["generated_text"]
                    if isinstance(gen, str):
                        return gen.strip()
                    elif isinstance(gen, list) and len(gen) > 0 and isinstance(gen[-1], dict) and "content" in gen[-1]:
                        return str(gen[-1]["content"]).strip()
                elif "summary_text" in first:
                    return str(first["summary_text"]).strip()
        return None
