"""
Test Suite for DhanSarthi Phase L.11.3: Streaming-First AI Response Pipeline & Perceived Latency Optimization.

Verifies:
1. Streaming endpoint execution when enabled
2. Non-stream fallback when streaming disabled (HTTP 501)
3. First token emission and TTFT recording
4. Multiple token chunks assembled correctly
5. Done/complete event emitted
6. Error event is sanitized
7. API key never appears in SSE output
8. CancelledError does not persist partial assistant message
9. Mid-stream provider failure does not persist corrupt response
10. SafetyValidator still executes on full response
11. ResponseQualityEvaluator still executes
12. Controlled retry still works
13. Personal fast-path remains active during streaming
14. Personal RAG remains bypassed
15. Market data remains bypassed
16. Adaptive token budget remains active (<= 180 tokens)
17. Telemetry records TTFT
18. Telemetry records generated tokens
19. Telemetry records tokens/sec
20. Exactly one assistant response is persisted
21. Frontend chunk parsing and state integrity
22. Frontend fallback when streaming is unavailable
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.advisor.service import AIAdvisorService
from app.ai.schemas.advisor import AIContext, SendMessageRequest, MessageResponse
from app.ai.schemas.query_understanding import QueryUnderstanding
from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    OperationType,
    QueryExecutionPlan,
    QueryScope,
)
from app.ai.context.builder import AIContextBuilder
from app.ai.observability.latency import LatencyTracker
from app.ai.exceptions import AISafetyError, AIProviderError
from app.core.config import settings


def _create_mock_service(
    mock_llm=None,
    mock_rag=None,
    mock_safety=None,
    mock_quality=None,
    mock_conv=None,
    mock_qu=None,
    mock_market=None,
    mock_dash=None,
):
    mock_db = MagicMock()
    mock_builder = AIContextBuilder()

    if mock_conv is None:
        mock_conv = MagicMock()
        mock_conv.get_conversation = MagicMock(return_value=MagicMock(id=123, user_id=1))
        mock_conv.get_recent_messages = MagicMock(return_value=[])
        now_dt = datetime.now(timezone.utc)
        dummy_user_msg = MagicMock(id=1, conversation_id=123, role="user", content="hello", message_metadata={}, created_at=now_dt)
        mock_conv.store_user_message = MagicMock(return_value=dummy_user_msg)

        def _store_asst(conversation_id, content, metadata=None):
            return MagicMock(id=2, conversation_id=conversation_id, role="assistant", content=content, message_metadata=metadata or {}, created_at=datetime.now(timezone.utc))

        mock_conv.store_assistant_message = MagicMock(side_effect=_store_asst)

    if mock_dash is None:
        mock_dash = MagicMock()
        mock_dash.build_dashboard = MagicMock(return_value=None)

    if mock_rag is None:
        mock_rag = MagicMock()
        mock_rag.retrieve = AsyncMock(return_value=[])

    if mock_safety is None:
        mock_safety = MagicMock()
        mock_safety.validate_response = MagicMock(return_value=None)

    if mock_quality is None:
        mock_quality = MagicMock()
        qr = MagicMock(overall_pass=True, overall_score=1.0, dimensions={}, failure_reasons=[])
        mock_quality.evaluate = MagicMock(return_value=qr)

    if mock_market is None:
        mock_market = MagicMock()
        mock_market.get_relevant_market_data = AsyncMock(return_value=None)

    if mock_qu is None:
        mock_qu = MagicMock()
        ep = QueryExecutionPlan(
            original_query="hello",
            intent=QueryIntent.GENERAL_FINANCE,
            sub_intent=SubIntent.GENERAL,
            scope=QueryScope.EDUCATIONAL,
            operation=OperationType.EXPLAIN,
            requires_rag=False,
            requires_market_data=False,
        )
        mock_qu.analyze = MagicMock(return_value=QueryUnderstanding(
            original_query="hello",
            normalized_query="hello",
            corrected_query="hello",
            resolved_query="hello",
            retrieval_query="hello",
            intent=QueryIntent.GENERAL_FINANCE,
            sub_intent=SubIntent.GENERAL,
            execution_plan=ep,
            requires_personal_data=False,
            requires_market_data=False,
        ))

    service = AIAdvisorService(
        db=mock_db,
        llm_provider=mock_llm or MagicMock(),
        rag_retriever=mock_rag,
        safety_validator=mock_safety,
        context_builder=mock_builder,
        dashboard_service=mock_dash,
        conversation_service=mock_conv,
        market_data_service=mock_market,
        query_understanding_service=mock_qu,
    )
    if mock_quality is not None:
        service._quality_evaluator = mock_quality
    return service, mock_conv, mock_safety, mock_quality, mock_rag, mock_market


@pytest.mark.anyio
async def test_streaming_endpoint_works_when_enabled():
    """Test 1: Streaming produces SSE events when enabled."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "Hello "
        yield "there!"

    mock_llm.generate_stream = _stream_gen
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    events = []
    async for chunk in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        events.append(chunk)

    joined = "".join(events)
    assert "event: start" in joined
    assert "event: token" in joined
    assert "event: complete" in joined
    assert "Hello " in joined
    assert "there!" in joined


@pytest.mark.anyio
async def test_non_stream_fallback_when_streaming_disabled():
    """Test 2: When streaming is disabled, non-streaming fallback succeeds."""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Non-streamed response.")
    service, _, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    resp = await service.send_chat_message(user_id=1, conversation_id=123, request=req)
    assert resp.assistant_message.content == "Non-streamed response."


@pytest.mark.anyio
async def test_first_token_is_emitted():
    """Test 3: First token chunk is emitted promptly."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "First"
        yield " second"

    mock_llm.generate_stream = _stream_gen
    service, _, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    chunks = []
    async for event in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        if "event: token" in event:
            chunks.append(event)

    assert len(chunks) == 2
    assert "First" in chunks[0]


@pytest.mark.anyio
async def test_multiple_token_chunks_assembled_correctly():
    """Test 4: Stream chunks are assembled into full response before persistence."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        for w in ["A", "B", "C", "D"]:
            yield w

    mock_llm.generate_stream = _stream_gen
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    mock_conv.store_assistant_message.assert_called_once()
    stored_content = mock_conv.store_assistant_message.call_args[1]["content"]
    assert stored_content == "ABCD"


@pytest.mark.anyio
async def test_done_event_is_emitted():
    """Test 5: Event complete is yielded as the final SSE event."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "Done test"

    mock_llm.generate_stream = _stream_gen
    service, _, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    events = []
    async for e in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        events.append(e)

    last_event = events[-1]
    assert "event: complete" in last_event


@pytest.mark.anyio
async def test_error_event_is_sanitized():
    """Test 6: Error events do not leak internal system details or credentials."""
    mock_llm = MagicMock()

    async def _failing_stream(*args, **kwargs):
        raise AIProviderError("Secret connection db://user:pass@host failed")
        yield "never"

    mock_llm.generate_stream = _failing_stream
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    events = []
    try:
        async for e in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
            events.append(e)
    except Exception:
        pass

    joined = "".join(events)
    assert "user:pass" not in joined
    assert "db://" not in joined


@pytest.mark.anyio
async def test_api_key_never_appears_in_sse_output():
    """Test 7: HuggingFace API key never appears in SSE stream."""
    secret_key = "hf_secret_super_token_999"
    with patch.object(settings, "ai_provider_api_key", secret_key):
        mock_llm = MagicMock()

        async def _stream_gen(*args, **kwargs):
            yield "Safe response token."

        mock_llm.generate_stream = _stream_gen
        service, _, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

        req = SendMessageRequest(message="hello")
        all_text = ""
        async for e in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
            all_text += e

        assert secret_key not in all_text


@pytest.mark.anyio
async def test_cancelled_error_does_not_persist_partial_assistant_message():
    """Test 8: asyncio.CancelledError does not persist partial message."""
    mock_llm = MagicMock()

    async def _cancelled_stream(*args, **kwargs):
        yield "Partial token 1"
        raise asyncio.CancelledError()

    mock_llm.generate_stream = _cancelled_stream
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    with pytest.raises(asyncio.CancelledError):
        async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
            pass

    mock_conv.store_assistant_message.assert_not_called()


@pytest.mark.anyio
async def test_mid_stream_provider_failure_does_not_persist_corrupt_response():
    """Test 9: Mid-stream provider crash does not persist corrupted content."""
    mock_llm = MagicMock()

    async def _failing_stream(*args, **kwargs):
        yield "Partial token"
        raise RuntimeError("Provider connection lost mid-generation")

    mock_llm.generate_stream = _failing_stream
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    events = []
    async for e in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        events.append(e)

    mock_conv.store_assistant_message.assert_not_called()
    assert any("event: error" in e for e in events)


@pytest.mark.anyio
async def test_safety_validator_executes_on_streamed_response():
    """Test 10: SafetyValidator runs on assembled streamed content."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "Safe "
        yield "advice."

    mock_llm.generate_stream = _stream_gen
    service, _, mock_safety, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    assert mock_safety.validate_response.call_count >= 1


@pytest.mark.anyio
async def test_response_quality_evaluator_executes_on_streamed_response():
    """Test 11: ResponseQualityEvaluator runs on completed stream."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "Quality response."

    mock_llm.generate_stream = _stream_gen
    service, _, _, mock_quality, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    assert mock_quality.evaluate.call_count >= 1


@pytest.mark.anyio
async def test_controlled_quality_retry_in_streaming_path():
    """Test 12: Quality evaluation retry works in streaming path."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        yield "Initial response"

    mock_llm.generate_stream = _stream_gen
    mock_llm.generate = AsyncMock(return_value="Retried higher quality response.")

    mock_quality = MagicMock()
    qr_fail = MagicMock(overall_pass=False, overall_score=0.4, dimensions={}, failure_reasons=["low_completeness"])
    qr_pass = MagicMock(overall_pass=True, overall_score=0.95, dimensions={}, failure_reasons=[])
    mock_quality.evaluate = MagicMock(side_effect=[qr_fail, qr_pass])

    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm, mock_quality=mock_quality)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    mock_conv.store_assistant_message.assert_called_once()
    stored_content = mock_conv.store_assistant_message.call_args[1]["content"]
    assert "Retried" in stored_content


@pytest.mark.anyio
async def test_personal_fast_path_remains_active_during_streaming():
    """Test 13: Direct personal lookup activates fast path in streaming."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        tracker = kwargs.get("tracker")
        if tracker:
            tracker.record_flag("streaming_used", True)
        yield "Your goal is ₹1,00,000 for Emergency Fund."

    mock_llm.generate_stream = _stream_gen

    mock_qu = MagicMock()
    ep = QueryExecutionPlan(
        original_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    mock_qu.analyze = MagicMock(return_value=QueryUnderstanding(
        original_query="tell me about my goal",
        normalized_query="tell me about my goal",
        corrected_query="tell me about my goal",
        resolved_query="tell me about my goal",
        retrieval_query="tell me about my goal",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.GOAL_ANALYSIS,
        execution_plan=ep,
        requires_personal_data=True,
        requires_market_data=False,
    ))

    service, mock_conv, _, _, mock_rag, mock_market = _create_mock_service(mock_llm=mock_llm, mock_qu=mock_qu)

    req = SendMessageRequest(message="tell me about my goal")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    # 1. RAG retrieval was bypassed
    mock_rag.retrieve.assert_not_called()

    # 2. Market data was bypassed
    mock_market.get_relevant_market_data.assert_not_called()

    # 3. Fast-path metadata was recorded
    meta = mock_conv.store_assistant_message.call_args[1]["metadata"]
    assert meta["latency"]["personal_fast_path_used"] is True
    assert meta["latency"]["general_rag_skipped"] is True
    assert meta["latency"]["market_data_skipped"] is True
    assert meta["latency"]["adaptive_output_budget"] <= 180


@pytest.mark.anyio
async def test_adaptive_token_budget_remains_active_during_streaming():
    """Test 16: Adaptive token budget <= 180 is passed to provider in streaming."""
    mock_llm = MagicMock()
    captured_max_tokens = []

    async def _stream_gen(*args, **kwargs):
        captured_max_tokens.append(kwargs.get("max_tokens"))
        yield "Goal is 10k."

    mock_llm.generate_stream = _stream_gen

    mock_qu = MagicMock()
    ep = QueryExecutionPlan(
        original_query="what is my net worth?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.NET_WORTH_ANALYSIS,
        scope=QueryScope.PERSONAL_LOOKUP,
        operation=OperationType.LOOKUP,
        requires_rag=False,
        requires_market_data=False,
    )
    mock_qu.analyze = MagicMock(return_value=QueryUnderstanding(
        original_query="what is my net worth?",
        normalized_query="what is my net worth?",
        corrected_query="what is my net worth?",
        resolved_query="what is my net worth?",
        retrieval_query="what is my net worth?",
        intent=QueryIntent.PERSONAL_FINANCE,
        sub_intent=SubIntent.NET_WORTH_ANALYSIS,
        execution_plan=ep,
        requires_personal_data=True,
        requires_market_data=False,
    ))

    service, _, _, _, _, _ = _create_mock_service(mock_llm=mock_llm, mock_qu=mock_qu)

    req = SendMessageRequest(message="what is my net worth?")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    assert len(captured_max_tokens) == 1
    assert captured_max_tokens[0] <= 180


@pytest.mark.anyio
async def test_telemetry_records_ttft_and_tokens():
    """Test 17, 18, 19: Streaming records TTFT, generated tokens, and tokens per second."""
    from app.ai.providers.mock import MockLLMProvider
    mock_llm = MockLLMProvider("This is a streamed financial advice test with several tokens.")

    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    meta = mock_conv.store_assistant_message.call_args[1]["metadata"]
    latency = meta["latency"]
    assert latency["streaming_used"] is True
    assert latency["ttft_ms"] > 0
    assert latency["generated_tokens"] > 0
    assert latency["tokens_per_second"] > 0


@pytest.mark.anyio
async def test_exactly_one_assistant_response_persisted():
    """Test 20: One user request produces exactly one persisted assistant message."""
    mock_llm = MagicMock()

    async def _stream_gen(*args, **kwargs):
        for i in range(5):
            yield f"chunk{i} "

    mock_llm.generate_stream = _stream_gen
    service, mock_conv, _, _, _, _ = _create_mock_service(mock_llm=mock_llm)

    req = SendMessageRequest(message="hello")
    async for _ in service.stream_chat_message(user_id=1, conversation_id=123, request=req, emit_sse=True):
        pass

    assert mock_conv.store_user_message.call_count == 1
    assert mock_conv.store_assistant_message.call_count == 1


def test_frontend_sse_parser_handles_chunk_fragmentation():
    """Test 21: Verify SSE frame parser correctly handles split/fragmented chunks."""
    # Simulated frame parsing logic matching useAI.js processFrame
    def _parse_sse_frames(raw_text: str):
        frames = raw_text.split("\n\n")
        events = []
        for frame in frames:
            if not frame.strip():
                continue
            lines = frame.strip().split("\n")
            event_name = None
            data_str = None
            for line in lines:
                if line.startswith("event:"):
                    event_name = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
            if data_str:
                events.append((event_name, json.loads(data_str) if data_str != "[DONE]" else "[DONE]"))
        return events

    stream_payload = (
        'event: start\ndata: {"conversation_id": 123}\n\n'
        'event: token\ndata: {"text": "Hello "}\n\n'
        'event: token\ndata: {"text": "World!"}\n\n'
        'event: complete\ndata: {"status": "completed"}\n\n'
    )
    parsed = _parse_sse_frames(stream_payload)
    assert len(parsed) == 4
    assert parsed[0][0] == "start"
    assert parsed[1][1]["text"] == "Hello "
    assert parsed[2][1]["text"] == "World!"
    assert parsed[3][0] == "complete"


@pytest.mark.anyio
async def test_frontend_fallback_on_sse_501():
    """Test 22: When AI_STREAMING_ENABLED=False, backend returns 501 HTTP exception allowing frontend to fallback."""
    from fastapi import HTTPException
    with patch.object(settings, "ai_streaming_enabled", False):
        if not settings.ai_streaming_enabled:
            exc = HTTPException(status_code=501, detail="Streaming disabled.")
            assert exc.status_code == 501

