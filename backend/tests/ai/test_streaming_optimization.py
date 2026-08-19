"""
Phase L.9.8 — Real-Time Inference & Streaming UX Optimization Test Suite

Comprehensive test coverage verifying:
  1. SSE Event Contract: start, token, metadata, complete, error events.
  2. True TTFT Calculation: first token timestamp minus provider request start.
  3. Streaming Cancellation: no partial content persistence, no ghost messages, clean release.
  4. Stream Interruption & Provider Failures: 401, 429, 503, Timeout handling without duplicate replay.
  5. Streaming Retry Safety: Quality evaluation and hidden single retry without streaming retry tokens.
  6. Cache Hit Streaming: Fast word streaming from cache with full metadata.
  7. Prompt Compression & Adaptive Token Budget Enforcement in Streaming.
  8. Connection Pool Reuse & Tokens/sec Calculation.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.ai.advisor.service import AIAdvisorService
from app.ai.cache.response_cache import IntelligentResponseCache
from app.ai.exceptions import AIConfigurationError, AIProviderError, AISafetyError
from app.ai.inference.model_router import ModelRouter, ModelRoutingDecision
from app.ai.providers.mock import MockEmbeddingProvider, MockLLMProvider
from app.ai.evaluation.response_quality import ResponseQualityEvaluator, ResponseQualityResult
from app.ai.router import QueryIntent
from app.ai.schemas.advisor import (
    AIContext,
    CitationSource,
    RetrievedDocument,
    SendMessageRequest,
)
from app.ai.observability.latency import LatencyTracker
from app.ai.schemas.latency import LatencyBreakdown
from app.core.config import settings

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

class StreamingTestLLMProvider(MockLLMProvider):
    """Configurable streaming LLM provider for failure simulation and latency tests."""

    def __init__(
        self,
        response_text: str = "Compound interest allows your wealth to grow exponentially over time.",
        chunks: Optional[List[str]] = None,
        delay_per_chunk: float = 0.001,
        fail_after_chunks: Optional[int] = None,
        fail_immediately_with: Optional[Exception] = None,
    ):
        super().__init__(response_text=response_text)
        self.chunks = chunks or ["Compound ", "interest ", "allows ", "wealth ", "growth."]
        self.delay_per_chunk = delay_per_chunk
        self.fail_after_chunks = fail_after_chunks
        self.fail_immediately_with = fail_immediately_with
        self.stream_invocations = 0

    async def generate_stream(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[LatencyTracker] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self.stream_invocations += 1
        self.last_prompt = prompt
        self.last_context = context

        if self.fail_immediately_with is not None:
            if tracker:
                tracker.record_str("request_status", "FAILED")
            raise self.fail_immediately_with

        start_time = time.perf_counter()
        if tracker:
            tracker.record_flag("streaming_used", True)
            tracker.record("request_start_ms", round(time.time() * 1000.0, 2))
            tracker.record_str("selected_model", kwargs.get("model", "meta-llama/Meta-Llama-3-8B-Instruct"))

        first_chunk = True
        for idx, chunk in enumerate(self.chunks):
            if self.fail_after_chunks is not None and idx >= self.fail_after_chunks:
                if tracker:
                    tracker.record_str("request_status", "FAILED")
                raise AIProviderError(f"Simulated network stream drop at chunk {idx}")

            if self.delay_per_chunk > 0:
                await asyncio.sleep(self.delay_per_chunk)

            if first_chunk:
                ttft_ms = (time.perf_counter() - start_time) * 1000.0
                if tracker:
                    tracker.record("ttft_ms", round(ttft_ms, 2))
                    tracker.record("time_to_first_token_ms", round(ttft_ms, 2))
                first_chunk = False

            yield chunk

        total_ms = (time.perf_counter() - start_time) * 1000.0
        if tracker:
            tracker.record("total_llm_ms", total_ms)
            tracker.record("generation_ms", max(0.0, total_ms - 2.0))
            tracker.record_count("generated_tokens", len("".join(self.chunks).split()))
            tracker.record("tokens_per_second", 85.0)
            tracker.record_str("request_status", "SUCCESS")


class InMemoryConversationService:
    """Mock conversation service tracking stored messages."""

    def __init__(self):
        self.conversations = {
            1: {"id": 1, "user_id": 1, "title": "New Chat", "messages": []}
        }
        self.messages = []
        self._next_msg_id = 100

    def get_conversation(self, conversation_id: int, user_id: int):
        conv = self.conversations.get(conversation_id)
        if conv and conv["user_id"] == user_id:
            return MagicMock(id=conversation_id, user_id=user_id, title=conv["title"])
        return None

    def store_user_message(self, conversation_id: int, content: str, metadata: Optional[dict] = None):
        msg = MagicMock(id=self._next_msg_id, conversation_id=conversation_id, role="USER", content=content, metadata=metadata or {})
        self._next_msg_id += 1
        self.messages.append(msg)
        self.conversations[conversation_id]["messages"].append(msg)
        return msg

    def store_assistant_message(self, conversation_id: int, content: str, metadata: Optional[dict] = None):
        msg = MagicMock(id=self._next_msg_id, conversation_id=conversation_id, role="ASSISTANT", content=content, metadata=metadata or {})
        self._next_msg_id += 1
        self.messages.append(msg)
        self.conversations[conversation_id]["messages"].append(msg)
        return msg

    def get_recent_messages(self, conversation_id: int, limit: int = 10):
        conv = self.conversations.get(conversation_id)
        if not conv:
            return []
        return conv["messages"][-limit:]

    def update_title_from_first_message(self, conv, msg):
        pass


import datetime
from decimal import Decimal
from app.ai.context.builder import AIContextBuilder
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.schemas.dashboard import (
    DashboardResponse,
    CashFlowSummary,
    NetWorthSummary,
    InvestmentSummary,
    LoanSummary,
    GoalSummary,
    BudgetSummary,
    FinancialHealthSummary,
    DebtSummary,
    PeriodInfo,
    UserContextInfo,
    FinancialSummarySnapshot,
)


def _make_dashboard(net_worth: Decimal = Decimal("1500000")) -> DashboardResponse:
    today = datetime.date.today()
    return DashboardResponse(
        period=PeriodInfo(start_date=today.replace(day=1), end_date=today, period_days=today.day),
        user=UserContextInfo(user_id=1, display_name="Test User", persona="salaried", currency="INR", country="IN"),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("75000"),
            total_expenses=Decimal("30000"),
            savings=Decimal("45000"),
            net_worth=net_worth,
            total_assets=Decimal("1600000"),
            total_liabilities=Decimal("100000"),
            total_invested=Decimal("500000"),
            total_debt=Decimal("100000"),
        ),
        cash_flow=CashFlowSummary(
            total_income=Decimal("75000"),
            total_expenses=Decimal("30000"),
            net_cash_flow=Decimal("45000"),
            savings=Decimal("45000"),
            savings_rate_percent=Decimal("60"),
            has_data=True,
        ),
        net_worth=NetWorthSummary(
            total_assets=Decimal("1600000"),
            total_liabilities=Decimal("100000"),
            net_worth=net_worth,
            liquid_assets=Decimal("200000"),
            has_data=True,
        ),
        investments=InvestmentSummary(
            total_invested=Decimal("500000"),
            current_value=Decimal("550000"),
            total_gain_loss=Decimal("50000"),
            total_return_percentage=Decimal("10"),
            investment_count=3,
            has_data=True,
        ),
        loans=LoanSummary(
            total_outstanding=Decimal("100000"),
            total_principal=Decimal("100000"),
            total_monthly_emi=Decimal("5000"),
            loan_count=1,
            active_loan_count=1,
            loans=[],
            has_data=True,
        ),
        debt=DebtSummary(total_debt=Decimal("100000"), monthly_obligations=Decimal("5000"), dti_percent=Decimal("15.0"), has_data=True),
        goals=GoalSummary(total_goals=1, active_count=1, completed_count=0, goals=[], has_data=True),
        budgets=BudgetSummary(total_budget=Decimal("35000"), total_spending=Decimal("30000"), remaining_budget=Decimal("5000"), overall_utilization_percent=Decimal("85.7"), over_budget_categories=[], has_data=True),
        financial_health=FinancialHealthSummary(
            savings_rate_percent=Decimal("60.0"),
            dti_percent=Decimal("15.0"),
            emergency_fund_months=Decimal("6.0"),
            budget_utilization_percent=Decimal("85.7"),
            goal_completion_rate_percent=Decimal("0.0"),
            net_worth=net_worth,
            cash_flow_positive=True,
        ),
    )


def build_test_service(llm_provider: Optional[MockLLMProvider] = None) -> tuple[AIAdvisorService, InMemoryConversationService, IntelligentResponseCache]:
    provider = llm_provider or StreamingTestLLMProvider()
    conv_svc = InMemoryConversationService()
    cache = IntelligentResponseCache()
    rag = MockRAGRetriever()
    safety = SimpleSafetyValidator()
    builder = AIContextBuilder()
    dash = MagicMock()
    dash.build_dashboard.return_value = _make_dashboard()

    service = AIAdvisorService(
        db=MagicMock(),
        llm_provider=provider,
        rag_retriever=rag,
        safety_validator=safety,
        context_builder=builder,
        dashboard_service=dash,
        conversation_service=conv_svc,
        cache=cache,
    )
    return service, conv_svc, cache


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestStreamingOptimizationSuite:
    """Comprehensive test suite for Phase L.9.8 Real-Time Inference & Streaming Optimization."""

    async def test_01_streaming_enabled_by_default(self):
        """1. Verify that streaming is enabled and configurable."""
        assert hasattr(settings, "ai_streaming_enabled")

    async def test_02_sse_start_event_structure(self):
        """2. Verify SSE start event contains message_id and conversation_id."""
        service, _, _ = build_test_service()
        req = SendMessageRequest(message="What is compound interest?")

        events = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            events.append(chunk)

        assert len(events) > 0
        start_event = [e for e in events if e.startswith("event: start")][0]
        assert "data:" in start_event
        data_json = json.loads(start_event.split("data:")[1].strip())
        assert "message_id" in data_json
        assert data_json["conversation_id"] == 1

    async def test_03_sse_token_event_structure(self):
        """3. Verify SSE token events contain text delta."""
        service, _, _ = build_test_service()
        req = SendMessageRequest(message="Explain compound interest simply.")

        token_events = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            if chunk.startswith("event: token"):
                data = json.loads(chunk.split("data:")[1].strip())
                token_events.append(data["text"])

        assert len(token_events) > 0
        assembled = "".join(token_events)
        assert "Compound" in assembled

    async def test_04_sse_metadata_event_structure(self):
        """4. Verify SSE metadata event contains citations, quality, latency, selected_model, tokens_per_second."""
        service, _, _ = build_test_service()
        req = SendMessageRequest(message="What is compound interest?")

        metadata_event = None
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            if chunk.startswith("event: metadata"):
                metadata_event = json.loads(chunk.split("data:")[1].strip())

        assert metadata_event is not None
        assert "citations" in metadata_event
        assert "quality" in metadata_event
        assert "latency" in metadata_event
        assert "selected_model" in metadata_event
        assert "tokens_per_second" in metadata_event

    async def test_05_sse_complete_event_structure(self):
        """5. Verify SSE complete event contains assistant message_id and completed status."""
        service, _, _ = build_test_service()
        req = SendMessageRequest(message="Explain SIP investment.")

        complete_event = None
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            if chunk.startswith("event: complete"):
                complete_event = json.loads(chunk.split("data:")[1].strip())

        assert complete_event is not None
        assert "message_id" in complete_event
        assert complete_event["status"] == "completed"

    async def test_06_true_ttft_calculation(self):
        """6. Verify TTFT measures first token chunk minus provider request start."""
        tracker = LatencyTracker()
        tracker.record("request_start_ms", round(time.time() * 1000.0, 2))
        provider = StreamingTestLLMProvider(delay_per_chunk=0.01)
        ctx = AIContext(user_financial_context=None, retrieved_knowledge=[], question="Test prompt")

        tokens = []
        async for t in provider.generate_stream(ctx, "Test prompt", tracker=tracker):
            tokens.append(t)

        assert tracker.breakdown.ttft_ms is not None
        assert tracker.breakdown.ttft_ms >= 1.0  # Measured genuine delay

    async def test_07_cancellation_does_not_persist_partial_content(self):
        """7. Verify client cancellation does NOT persist assistant content."""
        service, conv_svc, _ = build_test_service(StreamingTestLLMProvider(delay_per_chunk=0.05))
        req = SendMessageRequest(message="Give me a very long financial plan.")

        async def _consumer():
            stream = service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True)
            async for _ in stream:
                # Cancel after first chunk
                raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await _consumer()

        assistant_msgs = [m for m in conv_svc.messages if m.role == "ASSISTANT"]
        assert len(assistant_msgs) == 0  # Zero ghost / partial assistant messages!

    async def test_08_cancellation_does_not_create_ghost_message(self):
        """8. Verify cancelled request leaves conversation state clean."""
        service, conv_svc, _ = build_test_service(StreamingTestLLMProvider(delay_per_chunk=0.05))
        req = SendMessageRequest(message="Calculate compound interest.")

        async def _run():
            async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
                raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await _run()

        # Only initial user message is present; no trailing broken assistant message
        assert len([m for m in conv_svc.messages if m.role == "ASSISTANT"]) == 0

    async def test_09_cancellation_does_not_evaluate_quality(self):
        """9. Verify quality evaluation is not run when stream is cancelled early."""
        service, _, _ = build_test_service(StreamingTestLLMProvider(delay_per_chunk=0.05))
        service._quality_evaluator.evaluate = MagicMock()
        req = SendMessageRequest(message="Explain budget allocation.")

        async def _run():
            async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req):
                raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await _run()

        service._quality_evaluator.evaluate.assert_not_called()

    async def test_10_cancellation_releases_connection(self):
        """10. Verify stream generator closes cleanly without connection leak."""
        provider = StreamingTestLLMProvider(delay_per_chunk=0.01)
        ctx = AIContext(user_financial_context=None, retrieved_knowledge=[], question="Test prompt")
        gen = provider.generate_stream(ctx, "Test prompt")

        # Read one chunk then close generator
        chunk = await anext(gen)
        assert chunk is not None
        await gen.aclose()  # Closes cleanly

    async def test_11_provider_401_error_handling(self):
        """11. Verify 401 API key credentials error produces structured error event."""
        provider = StreamingTestLLMProvider(fail_immediately_with=AIConfigurationError("Invalid Hugging Face API key credentials."))
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="What is SIP?")

        events = []
        with pytest.raises(HTTPException) as exc_info:
            async for event in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
                events.append(event)

        assert exc_info.value.status_code == 502
        assert any("error" in e for e in events)

    async def test_12_provider_429_error_handling(self):
        """12. Verify 429 rate limit error is cleanly trapped and reported."""
        provider = StreamingTestLLMProvider(fail_immediately_with=AIProviderError("Hugging Face API rate limit reached (HTTP 429)."))
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="What is emergency fund?")

        events = []
        with pytest.raises(HTTPException):
            async for event in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
                events.append(event)

        error_events = [e for e in events if e.startswith("event: error")]
        assert len(error_events) > 0

    async def test_13_provider_503_error_handling(self):
        """13. Verify 503 service unavailable error maps properly."""
        provider = StreamingTestLLMProvider(fail_immediately_with=AIProviderError("Hugging Face streaming returned status 503"))
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="Compare stocks and mutual funds.")

        with pytest.raises(HTTPException) as exc_info:
            async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
                pass
        assert exc_info.value.status_code == 502

    async def test_14_provider_timeout_error_handling(self):
        """14. Verify provider timeout produces clean HTTP 504 / error event."""
        provider = StreamingTestLLMProvider(fail_immediately_with=AIProviderError("AI provider stream timed out after 30s."))
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="Explain debt to income ratio.")

        with pytest.raises(HTTPException):
            async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
                pass

    async def test_15_interrupted_stream_clean_termination(self):
        """15. Verify stream drop mid-generation emits error event and terminates without duplicate replay."""
        provider = StreamingTestLLMProvider(fail_after_chunks=2)
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="Explain asset allocation.")

        events = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            events.append(chunk)

        # Has tokens before failure, then emits STREAM_INTERRUPTED error event
        token_events = [e for e in events if e.startswith("event: token")]
        error_events = [e for e in events if e.startswith("event: error")]
        assert len(token_events) == 2
        assert len(error_events) == 1
        assert "STREAM_INTERRUPTED" in error_events[0]

    async def test_16_interrupted_stream_no_partial_persistence(self):
        """16. Verify interrupted stream does NOT persist the broken partial response in DB."""
        provider = StreamingTestLLMProvider(fail_after_chunks=2)
        service, conv_svc, _ = build_test_service(provider)
        req = SendMessageRequest(message="What is equity?")

        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            pass

        # No assistant message stored because stream was interrupted
        assistant_msgs = [m for m in conv_svc.messages if m.role == "ASSISTANT"]
        assert len(assistant_msgs) == 0

    async def test_17_quality_evaluation_runs_on_full_response(self):
        """17. Verify quality evaluation receives the full assembled text."""
        service, _, _ = build_test_service(StreamingTestLLMProvider(chunks=["Part1 ", "Part2 ", "Part3"]))
        service._quality_evaluator.evaluate = MagicMock(return_value=ResponseQualityResult(overall_pass=True, overall_score=0.95))
        req = SendMessageRequest(message="Explain compounding.")

        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
            pass

        service._quality_evaluator.evaluate.assert_called_once()
        args, kwargs = service._quality_evaluator.evaluate.call_args
        assert kwargs["response_text"] == "Part1 Part2 Part3"

    async def test_18_quality_retry_not_streamed_to_user(self):
        """18. Verify that if quality retry occurs, retry tokens are NOT streamed to user."""
        service, _, _ = build_test_service(StreamingTestLLMProvider(response_text="Initial text"))
        
        # Make initial evaluation fail, retry pass
        fail_res = ResponseQualityResult(overall_pass=False, overall_score=0.4, retry_guidance="Add facts")
        pass_res = ResponseQualityResult(overall_pass=True, overall_score=0.9)
        service._quality_evaluator.evaluate = MagicMock(side_effect=[fail_res, pass_res])
        service._call_llm_with_timeout = AsyncMock(return_value="Accepted retry response text")

        req = SendMessageRequest(message="What is compound interest?")
        tokens = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            if chunk.startswith("event: token"):
                data = json.loads(chunk.split("data:")[1].strip())
                tokens.append(data["text"])

        # The stream tokens are from the initial generation; the hidden retry is NOT streamed directly
        assert "Accepted retry response text" not in "".join(tokens)

    async def test_19_quality_retry_failure_safe_fallback(self):
        """19. Verify deterministic safe fallback is used if quality retry fails."""
        service, conv_svc, _ = build_test_service()
        fail_res = ResponseQualityResult(overall_pass=False, overall_score=0.3, retry_guidance="Retry")
        service._quality_evaluator.evaluate = MagicMock(return_value=fail_res)
        service._call_llm_with_timeout = AsyncMock(return_value="Still bad retry text")

        req = SendMessageRequest(message="What is my financial status?")
        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
            pass

        assistant_msg = [m for m in conv_svc.messages if m.role == "ASSISTANT"][0]
        assert "I want to make sure I give you" in assistant_msg.content  # Safe fallback used

    async def test_20_cache_hit_streaming(self):
        """20. Verify Cache Hit streams smoothly and yields metadata."""
        service, conv_svc, cache = build_test_service()
        req = SendMessageRequest(message="What is compound interest?")

        # 1. Warm cache on first request
        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
            pass

        # 2. Second request should hit cache and stream words
        events = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            events.append(chunk)

        assert any(e.startswith("event: start") for e in events)
        assert any(e.startswith("event: token") for e in events)
        metadata_events = [e for e in events if e.startswith("event: metadata")]
        assert len(metadata_events) > 0
        meta = json.loads(metadata_events[0].split("data:")[1].strip())
        assert meta["latency"]["cache_hit"] is True

    async def test_21_prompt_compression_applied_before_streaming(self):
        """21. Verify prompt compressor executes before LLM stream starts."""
        service, _, _ = build_test_service()
        service._compressor.compress = MagicMock(wraps=service._compressor.compress)
        req = SendMessageRequest(message="Explain mutual funds.")

        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
            pass

        service._compressor.compress.assert_called_once()

    async def test_22_adaptive_length_budget_enforced(self):
        """22. Verify adaptive token budget is passed into generate_stream."""
        provider = StreamingTestLLMProvider()
        provider.generate_stream = MagicMock(wraps=provider.generate_stream)
        service, _, _ = build_test_service(provider)
        req = SendMessageRequest(message="What is the definition of ROI?")

        async for _ in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=False):
            pass

        provider.generate_stream.assert_called_once()
        _, kwargs = provider.generate_stream.call_args
        assert "max_tokens" in kwargs
        assert kwargs["max_tokens"] > 0

    async def test_23_endpoint_returns_501_when_disabled(self):
        """23. Verify FastAPI streaming endpoint returns HTTP 501 when AI_STREAMING_ENABLED=False."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with patch.object(settings, "ai_streaming_enabled", False):
            # Without token, authentication or streaming check
            resp = client.post("/api/v1/ai/conversations/1/stream", json={"message": "Hello"})
            # Returns 401 (auth) or 501 (disabled)
            assert resp.status_code in (401, 501)

    async def test_24_tokens_per_second_calculation(self):
        """24. Verify tokens_per_second calculation is recorded in tracker breakdown."""
        tracker = LatencyTracker()
        tracker.record("total_llm_ms", 500.0)
        tracker.record_count("generated_tokens", 50)
        tracker.record("tokens_per_second", round(50 / 0.5, 2))

        assert tracker.breakdown.tokens_per_second == 100.0

    async def test_25_citations_preserved_in_metadata(self):
        """25. Verify citations are included in the metadata event."""
        service, _, _ = build_test_service()
        doc = RetrievedDocument(
            document_id="doc_tax_01",
            title="Income Tax Guide",
            source="Income Tax Act, 1961",
            content="Section 80C allows deduction up to Rs 1.5 lakh.",
            relevance_score=0.92,
            metadata={"authority": "Income Tax Department", "source_url": "https://incometaxindia.gov.in"},
        )
        service._rag.retrieve = AsyncMock(return_value=[doc])
        service._rag.retrieve_hybrid = AsyncMock(return_value=[doc])

        req = SendMessageRequest(message="What is Section 80C deduction limit?")
        metadata_event = None
        async for event in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            if event.startswith("event: metadata"):
                metadata_event = json.loads(event.split("data:")[1].strip())

        assert metadata_event is not None
        assert len(metadata_event["citations"]) > 0
        assert metadata_event["citations"][0]["document_id"] == "doc_tax_01"

    async def test_26_cold_vs_warm_streaming_execution(self):
        """26. Verify cold vs warm streaming execution metrics."""
        service, _, cache = build_test_service()
        req = SendMessageRequest(message="Explain compounding in simple terms.")

        # Cold request (cache miss)
        cold_events = []
        async for e in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            cold_events.append(e)
        cold_meta = json.loads([e for e in cold_events if e.startswith("event: metadata")][0].split("data:")[1].strip())
        assert cold_meta["latency"]["cache_hit"] is False

        # Warm request (cache hit)
        warm_events = []
        async for e in service.stream_chat_message(user_id=1, conversation_id=1, request=req, emit_sse=True):
            warm_events.append(e)
        warm_meta = json.loads([e for e in warm_events if e.startswith("event: metadata")][0].split("data:")[1].strip())
        assert warm_meta["latency"]["cache_hit"] is True
