"""
Phase L.9.9 — AI Production Resilience, Failure Recovery & Graceful Degradation Test Suite.

Validates:
  1. CircuitBreaker state transitions (CLOSED, OPEN, HALF_OPEN, reset).
  2. RetryPolicy deterministic filtering (429, 502, 503, 504, timeout vs 400, 401, 403, safety, cancellation).
  3. Exponential backoff and jitter bounds.
  4. Error sanitization and secret scrubbing.
  5. Model fallback coordination with AI_ALLOWED_MODELS.
  6. Personal Finance failure boundaries (zero hallucination of financial numbers).
  7. RAG graceful degradation.
  8. Streaming recovery and cancellation handling.
  9. ResilienceService coordination and deterministic fallback messages.
 10. ResilienceMetrics serialization and metadata integrity.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.ai.resilience.circuit_breaker import CircuitBreaker, get_llm_circuit_breaker
from app.ai.resilience.provider_fallback import (
    ModelFallbackCoordinator,
    classify_provider_failure,
    sanitize_error_message,
)
from app.ai.resilience.rag_fallback import RAGDegradationCoordinator
from app.ai.resilience.resilience_service import ResilienceService, get_resilience_service
from app.ai.resilience.retry_policy import RetryPolicy
from app.ai.resilience.streaming_recovery import (
    StreamingRecoveryManager,
    format_sse_error_event,
)
from app.ai.router import QueryIntent
from app.ai.schemas.resilience import (
    CircuitState,
    FallbackType,
    ResilienceFailureType,
    ResilienceMetrics,
)
from app.core.config import settings

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ==============================================================================
# 1. Circuit Breaker Tests
# ==============================================================================

def test_circuit_breaker_initial_state_is_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=5.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True
    assert cb.failure_count == 0


def test_circuit_breaker_transitions_to_open_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=5.0)
    
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    cb.record_failure(ResilienceFailureType.PROVIDER_UNAVAILABLE)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2

    cb.record_failure(ResilienceFailureType.NETWORK_TIMEOUT)
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3
    assert cb.can_execute() is False


def test_circuit_breaker_ignores_non_provider_failures_for_threshold():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=5.0)
    cb.record_failure(ResilienceFailureType.VALIDATION)
    cb.record_failure(ResilienceFailureType.CLIENT_CANCELLED)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_transitions_to_half_open_after_cooldown():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=0.1)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    time.sleep(0.15)
    # After cooldown, can_execute permits trial request and transitions to HALF_OPEN
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_circuit_breaker_half_open_success_closes_circuit():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=0.1, half_open_requests=1)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN

    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure_reopens_circuit():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=0.1)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN

    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_failure(ResilienceFailureType.PROVIDER_UNAVAILABLE)
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


def test_circuit_breaker_reset():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=60.0)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.can_execute() is True


# ==============================================================================
# 2. Retry Policy Tests
# ==============================================================================

def test_retry_policy_retries_transient_failures():
    policy = RetryPolicy(max_retries=2)
    assert policy.should_retry(ResilienceFailureType.RATE_LIMIT, 0) is True
    assert policy.should_retry(ResilienceFailureType.PROVIDER_UNAVAILABLE, 0) is True
    assert policy.should_retry(ResilienceFailureType.PROVIDER_TIMEOUT, 0) is True
    assert policy.should_retry(ResilienceFailureType.GENERATION_TIMEOUT, 0) is True
    assert policy.should_retry(ResilienceFailureType.NETWORK_TIMEOUT, 0) is True


def test_retry_policy_rejects_non_retryable_failures():
    policy = RetryPolicy(max_retries=2)
    assert policy.should_retry(ResilienceFailureType.AUTHENTICATION, 0) is False
    assert policy.should_retry(ResilienceFailureType.AUTHORIZATION, 0) is False
    assert policy.should_retry(ResilienceFailureType.VALIDATION, 0) is False
    assert policy.should_retry(ResilienceFailureType.CLIENT_CANCELLED, 0) is False
    assert policy.should_retry(ResilienceFailureType.UNKNOWN, 0) is False


def test_retry_policy_enforces_max_attempts():
    policy = RetryPolicy(max_retries=2)
    assert policy.should_retry(ResilienceFailureType.PROVIDER_TIMEOUT, 0) is True
    assert policy.should_retry(ResilienceFailureType.PROVIDER_TIMEOUT, 1) is True
    assert policy.should_retry(ResilienceFailureType.PROVIDER_TIMEOUT, 2) is False


def test_retry_policy_backoff_and_jitter_bounds():
    policy = RetryPolicy(base_delay=0.1, max_delay=1.0, jitter_max=0.05)
    
    delay_0 = policy.calculate_backoff(0)
    assert 0.1 <= delay_0 <= 0.15 + 0.01

    delay_1 = policy.calculate_backoff(1)
    assert 0.2 <= delay_1 <= 0.25 + 0.01

    delay_high = policy.calculate_backoff(10)
    assert delay_high <= 1.05 + 0.01


# ==============================================================================
# 3. Failure Classification & Sanitization Tests
# ==============================================================================

def test_classify_provider_failure_from_status_codes():
    exc_429 = HTTPException(status_code=429, detail="Too Many Requests")
    assert classify_provider_failure(exc_429) == ResilienceFailureType.RATE_LIMIT

    exc_502 = HTTPException(status_code=502, detail="Bad Gateway")
    assert classify_provider_failure(exc_502) == ResilienceFailureType.PROVIDER_UNAVAILABLE

    exc_503 = HTTPException(status_code=503, detail="Service Unavailable")
    assert classify_provider_failure(exc_503) == ResilienceFailureType.PROVIDER_UNAVAILABLE

    exc_504 = HTTPException(status_code=504, detail="Gateway Timeout")
    assert classify_provider_failure(exc_504) == ResilienceFailureType.PROVIDER_TIMEOUT

    exc_401 = HTTPException(status_code=401, detail="Unauthorized")
    assert classify_provider_failure(exc_401) == ResilienceFailureType.AUTHENTICATION

    exc_403 = HTTPException(status_code=403, detail="Forbidden")
    assert classify_provider_failure(exc_403) == ResilienceFailureType.AUTHORIZATION


def test_classify_provider_failure_from_timeout_exceptions():
    assert classify_provider_failure(asyncio.TimeoutError()) == ResilienceFailureType.PROVIDER_TIMEOUT
    assert classify_provider_failure(TimeoutError("Read timeout")) == ResilienceFailureType.PROVIDER_TIMEOUT


def test_sanitize_error_message_scrubs_bearer_and_secrets():
    raw_error = "Failed request to HF api: Bearer hf_1234567890abcdef1234567890abcdef on url https://api.hf.co?token=hf_secret_key"
    sanitized = sanitize_error_message(raw_error)
    assert "hf_1234567890abcdef1234567890abcdef" not in sanitized
    assert "hf_secret_key" not in sanitized
    assert "[REDACTED]" in sanitized


# ==============================================================================
# 4. Model Fallback Tests
# ==============================================================================

def test_model_fallback_coordinator_picks_allowed_fallback():
    coordinator = ModelFallbackCoordinator(allowed_models=["meta-llama/Meta-Llama-3-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"])
    fallback = coordinator.get_fallback_model("meta-llama/Meta-Llama-3-8B-Instruct", attempted_models={"meta-llama/Meta-Llama-3-8B-Instruct"})
    assert fallback == "mistralai/Mistral-7B-Instruct-v0.3"


def test_model_fallback_coordinator_returns_none_when_exhausted():
    coordinator = ModelFallbackCoordinator(allowed_models=["meta-llama/Meta-Llama-3-8B-Instruct"])
    fallback = coordinator.get_fallback_model("meta-llama/Meta-Llama-3-8B-Instruct", attempted_models={"meta-llama/Meta-Llama-3-8B-Instruct"})
    assert fallback is None


# ==============================================================================
# 5. RAG Graceful Degradation Tests
# ==============================================================================

def test_rag_degradation_coordinator():
    rag_coord = RAGDegradationCoordinator()
    assert rag_coord.handle_faiss_failure(RuntimeError("FAISS corrupt")) == FallbackType.PGVECTOR_FALLBACK
    assert rag_coord.handle_pgvector_failure(RuntimeError("DB disconnected")) == FallbackType.DETERMINISTIC_FALLBACK
    assert rag_coord.should_require_authoritative_grounding(QueryIntent.GENERAL_FINANCE, [], is_regulatory=True) is True
    assert rag_coord.should_require_authoritative_grounding(QueryIntent.CASUAL, [], is_regulatory=False) is False


# ==============================================================================
# 6. Streaming Recovery Tests
# ==============================================================================

def test_streaming_recovery_manager_format_error_event():
    mgr = StreamingRecoveryManager()
    sse_error = mgr.on_stream_interrupted(streamed_chunks_count=5, failure_reason="ReadTimeout")
    assert sse_error.startswith("event: error\ndata: ")
    payload = json.loads(sse_error.replace("event: error\ndata: ", "").strip())
    assert payload["code"] == "STREAM_INTERRUPTED"
    assert "interrupted" in payload["message"]


# ==============================================================================
# 7. Central Resilience Service & Safe Fallbacks Tests
# ==============================================================================

def test_resilience_service_deterministic_fallback_messages():
    service = ResilienceService()
    
    # Personal finance failure message (Zero Hallucination Guarantee)
    pf_msg = service.get_safe_fallback_message(context_type="personal_finance")
    assert "couldn't retrieve your financial data" in pf_msg
    assert "don't want to guess at your numbers" in pf_msg

    # Provider unavailable fallback
    prov_msg = service.get_safe_fallback_message(failure_type=ResilienceFailureType.PROVIDER_UNAVAILABLE)
    assert "temporarily unable to generate an AI response" in prov_msg

    # Rate limit fallback
    rl_msg = service.get_safe_fallback_message(failure_type=ResilienceFailureType.RATE_LIMIT)
    assert "experiencing high demand" in rl_msg


def test_resilience_metrics_metadata_serialization():
    metrics = ResilienceMetrics(
        circuit_state=CircuitState.OPEN,
        failure_type=ResilienceFailureType.PROVIDER_UNAVAILABLE,
        fallback_used=True,
        fallback_type=FallbackType.SAFE_FALLBACK,
        safe_fallback_used=True,
        retry_count=2,
    )
    meta = metrics.to_metadata_dict()
    assert meta["circuit_state"] == "OPEN"
    assert meta["failure_type"] == "PROVIDER_UNAVAILABLE"
    assert meta["fallback_used"] is True
    assert meta["fallback_type"] == "SAFE_FALLBACK"
    assert meta["safe_fallback_used"] is True
    assert meta["retry_count"] == 2


# ==============================================================================
# 8. Service Integration Tests (Advisor End-to-End Resilience)
# ==============================================================================

from datetime import datetime, timezone

def _make_mock_message(msg_id: int, conversation_id: int, role: str, content: str, metadata: dict):
    m = MagicMock()
    m.id = msg_id
    m.conversation_id = conversation_id
    m.role = role
    m.content = content
    m.message_metadata = metadata
    m.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return m


@pytest.mark.anyio
async def test_advisor_service_personal_finance_failure_returns_deterministic_safe_message():
    """Validates that when dashboard_service fails on personal query, LLM is never called to guess numbers."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_dash = MagicMock()
    # Financial engine failure simulation
    mock_dash.build_dashboard.side_effect = RuntimeError("Database connection pool exhausted")
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "What is my current net worth?", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
    )

    response = await service.send_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="What is my current net worth?"),
    )

    # Assert that LLM generate was NEVER called
    mock_llm.generate.assert_not_called()
    assert "couldn't retrieve your financial data" in response.assistant_message.content
    assert response.assistant_message.message_metadata["resilience"]["safe_fallback_used"] is True


@pytest.mark.anyio
async def test_advisor_service_circuit_breaker_open_returns_safe_fallback():
    """Validates that when circuit breaker is OPEN, safe deterministic fallback is returned instantly."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="Explain compounding interest",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "Explain compounding interest"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "Explain compounding interest", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN

    resilience_service = ResilienceService(circuit_breaker=cb)

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        resilience_service=resilience_service,
    )

    response = await service.send_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="Explain compounding interest"),
    )

    mock_llm.generate.assert_not_called()
    assert "temporarily unable to generate an AI response" in response.assistant_message.content
    assert response.assistant_message.message_metadata["resilience"]["circuit_state"] == "OPEN"
    assert response.assistant_message.message_metadata["resilience"]["safe_fallback_used"] is True


@pytest.mark.anyio
async def test_advisor_service_streaming_circuit_breaker_open():
    """Validates that streaming chat message streams safe fallback when circuit breaker is OPEN."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="Explain compounding interest",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "Explain compounding interest"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "Explain compounding interest", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure(ResilienceFailureType.PROVIDER_TIMEOUT)
    assert cb.state == CircuitState.OPEN

    resilience_service = ResilienceService(circuit_breaker=cb)

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        resilience_service=resilience_service,
    )

    chunks = []
    async for event in service.stream_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="Explain compounding interest"),
        emit_sse=True,
    ):
        chunks.append(event)

    full_stream = "".join(chunks)
    assert "event: start" in full_stream
    assert "temporarily" in full_stream
    assert "unable" in full_stream
    assert "event: metadata" in full_stream
    assert "event: complete" in full_stream


@pytest.mark.anyio
async def test_advisor_service_streaming_client_cancellation_no_persistence():
    """Validates that on client disconnect / asyncio.CancelledError, no assistant message is persisted to DB."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="Tell me about mutual funds",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "Tell me about mutual funds"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "Tell me about mutual funds", {})
    mock_conv.get_recent_messages.return_value = []

    async def _mock_stream(*args, **kwargs):
        yield "Mutual "
        yield "funds "
        raise asyncio.CancelledError("Client disconnected")

    mock_llm.generate_stream = _mock_stream

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
    )

    with pytest.raises(asyncio.CancelledError):
        async for _ in service.stream_chat_message(
            user_id=1,
            conversation_id=1,
            request=SendMessageRequest(message="Tell me about mutual funds"),
            emit_sse=True,
        ):
            pass

    # Verify that assistant message was NEVER stored
    mock_conv.store_assistant_message.assert_not_called()


@pytest.mark.anyio
async def test_advisor_service_streaming_provider_interruption_emits_error():
    """Validates that mid-stream provider failure emits sanitized error event and rolls back persistence."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="Explain inflation",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "Explain inflation"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "Explain inflation", {})
    mock_conv.get_recent_messages.return_value = []

    async def _mock_stream(*args, **kwargs):
        yield "Inflation "
        raise RuntimeError("Connection dropped by remote server")

    mock_llm.generate_stream = _mock_stream

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
    )

    chunks = []
    async for event in service.stream_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="Explain inflation"),
        emit_sse=True,
    ):
        chunks.append(event)

    full_stream = "".join(chunks)
    assert "event: error" in full_stream
    assert "STREAM_INTERRUPTED" in full_stream
    # No partial DB persistence
    mock_conv.store_assistant_message.assert_not_called()


@pytest.mark.anyio
async def test_advisor_service_rag_degradation_recorded_in_metadata():
    """Validates that RAG retrieval exceptions are caught gracefully and recorded in resilience metadata."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.schemas.advisor import SendMessageRequest

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="SIP is a systematic investment plan where you invest regular sums.")
    mock_rag = MagicMock()
    # Simulate vector DB failure
    mock_rag.retrieve.side_effect = RuntimeError("pgvector table locked")
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_builder.build_context.return_value = MagicMock(
        question="What is a SIP?",
        conversation_history=[],
        retrieved_knowledge=[],
        user_financial_context=None,
    )
    mock_builder.build_prompt.return_value = "What is a SIP?"
    mock_dash = MagicMock()
    mock_dash.build_dashboard.return_value = MagicMock()
    mock_conv = MagicMock()

    mock_conv.get_conversation.return_value = MagicMock(id=1, user_id=1, title="Test")
    mock_conv.store_user_message.return_value = _make_mock_message(10, 1, "user", "What is a SIP?", {})
    mock_conv.get_recent_messages.return_value = []
    mock_conv.store_assistant_message.side_effect = lambda conversation_id, content, metadata: _make_mock_message(
        11, conversation_id, "assistant", content, metadata
    )

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
    )

    response = await service.send_chat_message(
        user_id=1,
        conversation_id=1,
        request=SendMessageRequest(message="What is a SIP?"),
    )

    assert response.assistant_message.message_metadata["resilience"]["rag_degraded"] is True


def test_circuit_breaker_normal_path_overhead_under_one_ms():
    """Validates that CLOSED circuit breaker check takes < 0.1 ms (requirement: < 1 ms)."""
    cb = CircuitBreaker()
    start = time.perf_counter()
    for _ in range(1000):
        assert cb.can_execute() is True
    elapsed_per_call_ms = ((time.perf_counter() - start) / 1000) * 1000.0
    assert elapsed_per_call_ms < 0.1


def test_sanitize_error_message_with_empty_or_non_string():
    assert sanitize_error_message("") == ""
    assert "[REDACTED]" in sanitize_error_message("Error: api_key='secret12345678'")


def test_resilience_service_can_execute_and_classify():
    service = ResilienceService()
    assert service.can_execute_llm() is True
    assert service.classify_failure(HTTPException(status_code=429)) == ResilienceFailureType.RATE_LIMIT


def test_retry_policy_exponential_backoff_monotonic_increase():
    """Validates that base backoff doubles exponentially with attempt count."""
    policy = RetryPolicy(base_delay=0.2, max_delay=10.0, jitter_max=0.0)
    b0 = policy.calculate_backoff(0)
    b1 = policy.calculate_backoff(1)
    b2 = policy.calculate_backoff(2)
    assert b0 == 0.2
    assert b1 == 0.4
    assert b2 == 0.8


@pytest.mark.anyio
async def test_model_fallback_during_transient_failure():
    """Validates that _call_llm_with_timeout falls back to secondary model on 503."""
    from app.ai.advisor.service import AIAdvisorService
    from app.ai.inference.model_router import ModelRoutingDecision

    mock_db = MagicMock()
    mock_llm = MagicMock()
    # First call with primary model fails with 503, second call with fallback model succeeds
    calls = []
    async def _mock_generate(*args, **kwargs):
        routing = kwargs.get("routing_decision")
        calls.append(routing.model if routing else "default")
        if len(calls) == 1:
            raise HTTPException(status_code=503, detail="Service Unavailable")
        return "Response from fallback model"

    mock_llm.generate = _mock_generate

    mock_rag = MagicMock()
    mock_safety = MagicMock()
    mock_builder = MagicMock()
    mock_dash = MagicMock()
    mock_conv = MagicMock()

    coordinator = ModelFallbackCoordinator(
        allowed_models=["meta-llama/Meta-Llama-3-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"]
    )
    resilience_service = ResilienceService(model_fallback=coordinator)

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm,
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        resilience_service=resilience_service,
    )

    routing = ModelRoutingDecision(
        tier="PRIMARY",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        complexity="MODERATE",
        reason="DEFAULT",
    )
    metrics = ResilienceMetrics()

    res = await service._call_llm_with_timeout(
        ai_context=MagicMock(),
        prompt="Hello",
        routing_decision=routing,
        resilience_metrics=metrics,
    )

    assert res == "Response from fallback model"
    assert len(calls) == 2
    assert calls[0] == "meta-llama/Meta-Llama-3-8B-Instruct"
    assert calls[1] == "mistralai/Mistral-7B-Instruct-v0.3"
    assert metrics.fallback_used is True
    assert metrics.fallback_type == FallbackType.MODEL_FALLBACK
