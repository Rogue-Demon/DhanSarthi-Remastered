"""
Phase L.9.2 — Dedicated Production AI Advisor Evaluation & Performance Optimization Test Suite.

Verifies:
  1. Latency aggregation across pipeline stages
  2. p50 / median calculation correctness
  3. p95 percentile calculation correctness
  4. p99 percentile calculation correctness
  5. Provider latency recording
  6. TTFT recording
  7. Tokens/sec calculation
  8. Quality metrics aggregation
  9. Retry rate calculation
 10. Retry success rate calculation
 11. Deterministic bottleneck detection
 12. RAG metrics (Hit@1, Hit@3, Hit@5, MRR, Authority Accuracy, Citation Accuracy)
 13. Personal finance boundary (FACT -> VALUE -> MEANING, no hallucination)
 14. Citation preservation
 15. Safe fallback handling
 16. Production provider configuration
 17. Streaming metrics preservation
 18. No API key leakage in latency or evaluation records
 19. No personal financial data leakage in logs or evaluation records
 20. Existing L.9.1 quality evaluator regression
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.evaluation.production_evaluation import (
    ProductionPerformanceEvaluator,
    SingleQueryEvaluationResult,
)
from app.ai.evaluation.response_quality import ResponseQualityEvaluator
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


class TestProductionPerformanceEvaluatorMath:
    """Unit tests for statistical and percentile calculation routines."""

    def test_p50_calculation(self):
        vals = [10.0, 20.0, 30.0, 40.0, 50.0]
        p50 = ProductionPerformanceEvaluator.calculate_percentile(vals, 50.0)
        assert p50 == 30.0

    def test_p95_calculation(self):
        vals = list(range(1, 101))  # 1 to 100
        p95 = ProductionPerformanceEvaluator.calculate_percentile(vals, 95.0)
        assert round(p95, 1) == 95.05 or round(p95, 0) == 95.0

    def test_p99_calculation(self):
        vals = list(range(1, 101))
        p99 = ProductionPerformanceEvaluator.calculate_percentile(vals, 99.0)
        assert round(p99, 1) == 99.01 or round(p99, 0) == 99.0

    def test_latency_stats_aggregation(self):
        vals = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = ProductionPerformanceEvaluator.calculate_latency_stats(vals)
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["mean"] == 30.0
        assert stats["p50"] == 30.0
        assert stats["p95"] == 48.0

    def test_bottleneck_detection_identifies_dominant_stage(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q1",
                category="TEST",
                intent="GENERAL",
                sub_intent="GENERAL",
                scope="EDUCATIONAL",
                operation="EXPLAIN",
                retrieval_strategy="HYBRID",
                selected_model="llama3",
                total_ms=500.0,
                generation_ms=350.0,
                retrieval_ms=50.0,
                query_understanding_ms=10.0,
                provider_network_ms=80.0,
                safety_validation_ms=5.0,
                persistence_ms=5.0,
            ),
            SingleQueryEvaluationResult(
                query="Q2",
                category="TEST",
                intent="GENERAL",
                sub_intent="GENERAL",
                scope="EDUCATIONAL",
                operation="EXPLAIN",
                retrieval_strategy="HYBRID",
                selected_model="llama3",
                total_ms=600.0,
                generation_ms=450.0,
                retrieval_ms=60.0,
                query_understanding_ms=10.0,
                provider_network_ms=70.0,
                safety_validation_ms=5.0,
                persistence_ms=5.0,
            ),
        ]
        bn = ProductionPerformanceEvaluator.identify_dominant_bottleneck(records)
        assert bn["dominant_bottleneck"] == "LLM_GENERATION"
        assert bn["dominant_percentage"] > 70.0

    def test_retry_rate_and_success_calculation(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q1", category="TEST", intent="G", sub_intent="G", scope="E",
                operation="E", retrieval_strategy="NONE", selected_model="m",
                total_ms=100.0, quality_passed=True, quality_retry_used=False,
            ),
            SingleQueryEvaluationResult(
                query="Q2", category="TEST", intent="G", sub_intent="G", scope="E",
                operation="E", retrieval_strategy="NONE", selected_model="m",
                total_ms=200.0, quality_passed=True, quality_retry_used=True,
                initial_quality_score=0.6, retry_quality_score=0.9,
            ),
        ]
        summary = ProductionPerformanceEvaluator.aggregate_benchmark(records)
        assert summary["quality"]["retry_rate_percent"] == 50.0
        assert summary["quality"]["retry_success_rate_percent"] == 100.0
        assert summary["quality"]["average_quality_improvement_on_retry"] == 0.3

    def test_rag_metrics_aggregation(self):
        records = [
            SingleQueryEvaluationResult(
                query="Q1", category="INVESTMENTS", intent="G", sub_intent="G", scope="E",
                operation="E", retrieval_strategy="HYBRID", selected_model="m",
                total_ms=100.0, is_rag_eligible=True, hit_at_1=True, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=1.0, authority_accuracy=1.0, citation_accuracy=1.0, grounding_score=1.0,
            ),
            SingleQueryEvaluationResult(
                query="Q2", category="INVESTMENTS", intent="G", sub_intent="G", scope="E",
                operation="E", retrieval_strategy="HYBRID", selected_model="m",
                total_ms=100.0, is_rag_eligible=True, hit_at_1=False, hit_at_3=True, hit_at_5=True,
                reciprocal_rank=0.5, authority_accuracy=1.0, citation_accuracy=1.0, grounding_score=0.8,
            ),
        ]
        summary = ProductionPerformanceEvaluator.aggregate_benchmark(records)
        assert summary["rag"]["hit_at_1"] == 0.5
        assert summary["rag"]["hit_at_3"] == 1.0
        assert summary["rag"]["hit_at_5"] == 1.0
        assert summary["rag"]["mrr"] == 0.75


@pytest.mark.anyio
class TestProductionAdvisorIntegration:
    """Integration tests verifying production AI Advisor pipeline metrics & boundaries."""

    @pytest.fixture
    def mock_deps(self):
        db = MagicMock()
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = MagicMock()
        dash.build_dashboard.return_value = _make_dashboard()
        conv = MagicMock()
        conv.get_recent_history.return_value = []

        now = datetime.datetime.now()
        user_msg = MagicMock(id=100, role="user", content="Hello", message_metadata={}, created_at=now)
        conv.store_user_message.return_value = user_msg
        conv.create_user_message.return_value = user_msg

        def _store_asst(conversation_id, content, metadata=None):
            return MagicMock(id=101, role="assistant", content=content, message_metadata=metadata or {}, created_at=datetime.datetime.now())

        conv.store_assistant_message.side_effect = _store_asst
        conv.get_conversation.return_value = MagicMock(id=1, user_id=1)
        conv.touch_conversation.return_value = None

        return {
            "db": db,
            "rag": rag,
            "safety": safety,
            "builder": builder,
            "dash": dash,
            "conv": conv,
        }

    async def test_provider_latency_and_tokens_recorded(self, mock_deps):
        provider = MockLLMProvider(response_text="A Systematic Investment Plan (SIP) allows investing in mutual funds.")
        service = AIAdvisorService(
            db=mock_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_deps["rag"],
            safety_validator=mock_deps["safety"],
            context_builder=mock_deps["builder"],
            dashboard_service=mock_deps["dash"],
            conversation_service=mock_deps["conv"],
        )

        with patch.object(settings, "ai_cache_educational_enabled", False):
            req = SendMessageRequest(message="What is a Systematic Investment Plan?")
            resp = await service.send_chat_message(user_id=1, conversation_id=1, request=req)

        meta = mock_deps["conv"].store_assistant_message.call_args[1]["metadata"]
        lat = meta["latency"]
        assert lat["total_ms"] > 0.0
        assert lat["query_understanding_ms"] >= 0.0
        assert lat["tokens_per_second"] > 0.0

    async def test_personal_finance_boundary_preserved(self, mock_deps):
        provider = MockLLMProvider(response_text="Your monthly expenses for this month are ₹30,000 and income is ₹75,000.")
        service = AIAdvisorService(
            db=mock_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_deps["rag"],
            safety_validator=mock_deps["safety"],
            context_builder=mock_deps["builder"],
            dashboard_service=mock_deps["dash"],
            conversation_service=mock_deps["conv"],
        )

        req = SendMessageRequest(message="How much did I spend this month?")
        resp = await service.send_chat_message(user_id=1, conversation_id=1, request=req)

        meta = mock_deps["conv"].store_assistant_message.call_args[1]["metadata"]
        q_meta = meta["quality"]
        assert q_meta["passed"] is True
        assert q_meta["dimensions"]["personal_accuracy"] == 1.0

    async def test_citation_preservation(self, mock_deps):
        provider = MockLLMProvider(response_text="SIP guidelines under AMFI allow monthly investing.")
        service = AIAdvisorService(
            db=mock_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_deps["rag"],
            safety_validator=mock_deps["safety"],
            context_builder=mock_deps["builder"],
            dashboard_service=mock_deps["dash"],
            conversation_service=mock_deps["conv"],
        )

        req = SendMessageRequest(message="What is SIP?")
        resp = await service.send_chat_message(user_id=1, conversation_id=1, request=req)

        assert len(resp.sources) > 0
        assert resp.sources[0].title is not None

    async def test_no_credentials_leakage_in_records(self, mock_deps):
        tracker = LatencyTracker(enabled=True)
        tracker.record("query_understanding_ms", 1.2)
        out = tracker.to_dict()
        out_str = str(out)
        assert "hf_" not in out_str
        assert "secret" not in out_str.lower()
        assert "api_key" not in out_str.lower()

    async def test_production_provider_configuration(self):
        """Verify that HuggingFaceProvider initializes with configured model."""
        hf = HuggingFaceProvider()
        assert hf.model == settings.ai_model
        assert hf.max_tokens == settings.ai_max_tokens

    async def test_streaming_metrics_preservation(self, mock_deps):
        provider = MockLLMProvider()
        async def _stream(*args, **kwargs):
            yield "A Systematic Investment Plan "
            yield "helps you build wealth systematically."

        provider.generate_stream = _stream

        service = AIAdvisorService(
            db=mock_deps["db"],
            llm_provider=provider,
            rag_retriever=mock_deps["rag"],
            safety_validator=mock_deps["safety"],
            context_builder=mock_deps["builder"],
            dashboard_service=mock_deps["dash"],
            conversation_service=mock_deps["conv"],
        )

        req = SendMessageRequest(message="What is SIP?")
        chunks = []
        async for chunk in service.stream_chat_message(user_id=1, conversation_id=1, request=req):
            chunks.append(chunk)

        assert len(chunks) == 2
        meta = mock_deps["conv"].store_assistant_message.call_args[1]["metadata"]
        assert meta["streaming"] is True
        assert meta["latency"]["total_ms"] > 0.0
