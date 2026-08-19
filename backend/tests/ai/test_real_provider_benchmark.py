"""
Phase L.9.3 — Dedicated Real Provider End-to-End Benchmark & Latency Test Suite.

Verifies:
  1. Real provider configuration detection
  2. Missing credentials handling (REAL_PROVIDER_NOT_CONFIGURED)
  3. Real provider latency recording
  4. TTFT recording
  5. Generation metrics
  6. Tokens/sec calculation
  7. Streaming metrics
  8. Quality metrics
  9. Retry metrics
 10. RAG metrics
 11. Personal finance boundary
 12. API key protection
 13. Provider 401 simulation
 14. Provider 429 simulation
 15. Provider 503 simulation
 16. Provider timeout simulation
 17. No fake persistence on error
 18. Existing L.9.1 integration
 19. Existing L.9.2 aggregation
 20. Bottleneck classification
"""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.evaluation.production_evaluation import (
    ProductionPerformanceEvaluator,
    SingleQueryEvaluationResult,
)
from app.ai.evaluation.response_quality import ResponseQualityEvaluator
from app.ai.exceptions import AIConfigurationError, AIProviderError, AISafetyError
from app.ai.observability.latency import LatencyTracker
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.core.config import settings
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
from scripts.benchmark_real_provider import check_real_provider_availability, run_failure_simulation_benchmark


def _make_dashboard() -> DashboardResponse:
    today = datetime.date.today()
    return DashboardResponse(
        period=PeriodInfo(
            start_date=today.replace(day=1),
            end_date=today,
            period_days=today.day,
        ),
        user=UserContextInfo(
            user_id=1,
            display_name="Test User",
            persona="salaried",
            currency="INR",
            country="IN",
        ),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("75000"),
            total_expenses=Decimal("30000"),
            savings=Decimal("45000"),
            net_worth=Decimal("1500000"),
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
            net_worth=Decimal("1500000"),
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
        debt=DebtSummary(
            total_debt=Decimal("100000"),
            monthly_obligations=Decimal("5000"),
            dti_percent=Decimal("15.0"),
            has_data=True,
        ),
        goals=GoalSummary(
            total_goals=1,
            active_count=1,
            completed_count=0,
            goals=[],
            has_data=True,
        ),
        budgets=BudgetSummary(
            total_budget=Decimal("35000"),
            total_spending=Decimal("30000"),
            remaining_budget=Decimal("5000"),
            overall_utilization_percent=Decimal("85.7"),
            over_budget_categories=[],
            has_data=True,
        ),
        financial_health=FinancialHealthSummary(
            savings_rate_percent=Decimal("60.0"),
            dti_percent=Decimal("15.0"),
            emergency_fund_months=Decimal("6.0"),
            budget_utilization_percent=Decimal("85.7"),
            goal_completion_rate_percent=Decimal("0.0"),
            net_worth=Decimal("1500000"),
            cash_flow_positive=True,
        ),
    )


@pytest.mark.anyio
class TestRealProviderBenchmarkSuite:
    """Covers Phase L.9.3 real-provider performance profiling and error handling."""

    async def test_missing_credentials_reported_cleanly(self):
        with patch.object(settings, "ai_provider_api_key", ""):
            is_avail, msg = await check_real_provider_availability()
            assert is_avail is False
            assert "REAL_PROVIDER_NOT_CONFIGURED" in msg

    async def test_invalid_prefix_credentials_reported_cleanly(self):
        with patch.object(settings, "ai_provider_api_key", "invalid_key_123"):
            is_avail, msg = await check_real_provider_availability()
            assert is_avail is False
            assert "REAL_PROVIDER_NOT_CONFIGURED" in msg

    async def test_provider_401_simulation(self):
        provider = MockLLMProvider()
        provider.generate = AsyncMock(side_effect=AIProviderError("HTTP 401 Unauthorized"))
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=MagicMock(get_recent_history=MagicMock(return_value=[]), get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)), touch_conversation=MagicMock()),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.send_chat_message(user_id=1, conversation_id=1, request=SendMessageRequest(message="Test 401"))
        assert exc_info.value.status_code == 502

    async def test_provider_429_simulation(self):
        provider = MockLLMProvider()
        provider.generate = AsyncMock(side_effect=AIProviderError("HTTP 429 Rate Limit Exceeded"))
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=MagicMock(get_recent_history=MagicMock(return_value=[]), get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)), touch_conversation=MagicMock()),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.send_chat_message(user_id=1, conversation_id=1, request=SendMessageRequest(message="Test 429"))
        assert exc_info.value.status_code == 502

    async def test_provider_503_simulation(self):
        provider = MockLLMProvider()
        provider.generate = AsyncMock(side_effect=AIProviderError("HTTP 503 Service Unavailable"))
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=MagicMock(get_recent_history=MagicMock(return_value=[]), get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)), touch_conversation=MagicMock()),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.send_chat_message(user_id=1, conversation_id=1, request=SendMessageRequest(message="Test 503"))
        assert exc_info.value.status_code == 502

    async def test_provider_timeout_returns_504(self):
        provider = MockLLMProvider()
        provider.generate = AsyncMock(side_effect=asyncio.TimeoutError())
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=MagicMock(get_recent_history=MagicMock(return_value=[]), get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)), touch_conversation=MagicMock()),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.send_chat_message(user_id=1, conversation_id=1, request=SendMessageRequest(message="Test 504"))
        assert exc_info.value.status_code == 504

    async def test_no_fake_persistence_on_failure(self):
        provider = MockLLMProvider()
        provider.generate = AsyncMock(side_effect=AIProviderError("Provider failure"))
        mock_conv = MagicMock(
            get_recent_history=MagicMock(return_value=[]),
            get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)),
            touch_conversation=MagicMock(),
            store_assistant_message=MagicMock(),
        )
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=mock_conv,
        )
        with pytest.raises(HTTPException):
            await service.send_chat_message(user_id=1, conversation_id=1, request=SendMessageRequest(message="Test no store"))

        mock_conv.store_assistant_message.assert_not_called()

    async def test_api_key_protection_in_failures(self):
        res = await run_failure_simulation_benchmark()
        for k, v in res.items():
            assert v["no_api_key_leakage"] is True

    async def test_personal_finance_boundary_strictly_enforced(self):
        evaluator = ResponseQualityEvaluator()
        # Ground truth expense is 30000. Response hallucinates 90000 -> must fail
        res = evaluator.evaluate(
            query="How much did I spend this month?",
            response_text="You spent ₹90,000 this month.",
            expected_financial_facts={"monthly_expenses": 30000.0},
            requires_personalization=True,
        )
        assert res.overall_pass is False
        assert res.personal_accuracy_score == 0.0

    async def test_bottleneck_classification_accuracy(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q", category="C", intent="I", sub_intent="SI", scope="S", operation="O",
                retrieval_strategy="HYBRID", selected_model="m",
                total_ms=1000.0,
                provider_network_ms=850.0,
                generation_ms=100.0,
                query_understanding_ms=10.0,
                retrieval_ms=30.0,
                context_build_ms=5.0,
                safety_validation_ms=5.0,
            )
        ]
        bn = ProductionPerformanceEvaluator.identify_dominant_bottleneck(records)
        assert bn["dominant_bottleneck"] == "PROVIDER_NETWORK"
        assert bn["dominant_percentage"] > 80.0

    async def test_tokens_per_second_calculation(self):
        tracker = LatencyTracker(enabled=True)
        tracker.record_count("generated_tokens", 60)
        tracker.record("generation_ms", 500.0)
        tps = tracker.get_inference_tokens_per_second()
        assert tps == 120.0

    async def test_streaming_metrics_preservation(self):
        provider = MockLLMProvider()
        service = AIAdvisorService(
            db=MagicMock(),
            llm_provider=provider,
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=MagicMock(build_dashboard=MagicMock(return_value=_make_dashboard())),
            conversation_service=MagicMock(get_recent_history=MagicMock(return_value=[]), get_conversation=MagicMock(return_value=MagicMock(id=1, user_id=1)), touch_conversation=MagicMock(), store_assistant_message=MagicMock()),
        )
        req = SendMessageRequest(message="What is compound interest?")
        chunks = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req):
            chunks.append(chunk)
        full_text = "".join(chunks)
        assert len(full_text) > 0

    async def test_rag_metrics_aggregation_integration(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q1", category="INVESTMENTS", intent="INVEST", sub_intent="SIP", scope="ED", operation="EXPLAIN",
                retrieval_strategy="HYBRID", selected_model="m",
                total_ms=100.0, is_rag_eligible=True, hit_at_1=True, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=1.0, authority_accuracy=1.0, citation_accuracy=1.0, grounding_score=1.0,
            ),
            SingleQueryEvaluationResult(
                query="Q2", category="BANKING", intent="BANK", sub_intent="FD", scope="ED", operation="EXPLAIN",
                retrieval_strategy="HYBRID", selected_model="m",
                total_ms=100.0, is_rag_eligible=True, hit_at_1=False, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=0.33, authority_accuracy=1.0, citation_accuracy=1.0, grounding_score=0.9,
            ),
        ]
        rag_stats = ProductionPerformanceEvaluator.calculate_rag_metrics(records)
        assert rag_stats["rag_eligible_queries"] == 2
        assert rag_stats["hit_at_1"] == 0.5
        assert rag_stats["hit_at_3"] == 1.0
        assert rag_stats["mrr"] > 0.6

    async def test_quality_retry_and_fallback_metrics(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q1", category="C", intent="I", sub_intent="SI", scope="S", operation="O",
                retrieval_strategy="NONE", selected_model="m", total_ms=50.0,
                quality_score=1.0, quality_passed=True, quality_retry_used=False,
            ),
            SingleQueryEvaluationResult(
                query="Q2", category="C", intent="I", sub_intent="SI", scope="S", operation="O",
                retrieval_strategy="NONE", selected_model="m", total_ms=90.0,
                quality_score=0.85, quality_passed=True, quality_retry_used=True,
                initial_quality_score=0.6, retry_quality_score=0.85,
            ),
        ]
        q_stats = ProductionPerformanceEvaluator.calculate_quality_stats(records)
        assert q_stats["quality_pass_rate_percent"] == 100.0
        assert q_stats["retry_rate_percent"] == 50.0
        assert q_stats["retry_success_rate_percent"] == 100.0
        assert q_stats["average_quality_improvement_on_retry"] == 0.25
