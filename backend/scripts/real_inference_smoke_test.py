"""
Phase L.9.4 — Real Inference Smoke Test Script.

Executes a single real test query ("What is a SIP?") through the complete
end-to-end AI Advisor pipeline using the configured real Hugging Face provider.

Pipeline:
  User Query
    ↓
  Query Understanding (L.1 - L.3)
    ↓
  Adaptive Retrieval Router (L.6)
    ↓
  RAG Retrieval (pgvector + FAISS)
    ↓
  Context Optimizer & Builder (L.7.4)
    ↓
  Model Selection (L.8)
    ↓
  HuggingFaceProvider (L.7.3)
    ↓
  SafetyValidator
    ↓
  ResponseQualityEvaluator (L.9.1)
    ↓
  Persistence

If the real provider is unavailable or blocked, fails safely with REAL_INFERENCE_BLOCKED.
"""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict
from unittest.mock import MagicMock

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.provider_readiness import ProviderReadinessService, ProviderReadinessStatus
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


def _build_smoke_dashboard() -> DashboardResponse:
    today = datetime.date.today()
    return DashboardResponse(
        period=PeriodInfo(
            start_date=today.replace(day=1),
            end_date=today,
            period_days=today.day,
        ),
        user=UserContextInfo(
            user_id=1,
            display_name="Smoke Test User",
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


async def run_real_inference_smoke_test() -> Dict[str, Any]:
    print("=" * 70, flush=True)
    print("DhanSarthi Real LLM Inference Smoke Test", flush=True)
    print(f"Provider: {settings.ai_provider} | Target Model: {settings.ai_model}", flush=True)
    print("=" * 70, flush=True)

    readiness = ProviderReadinessService()
    diag = await readiness.check_huggingface()

    if diag.status != ProviderReadinessStatus.READY:
        print(f"\nREAL_INFERENCE_BLOCKED: Provider is not ready ({diag.status.value}).", flush=True)
        print(f"Details: {diag.safe_error_message}", flush=True)
        report = {
            "status": "REAL_INFERENCE_BLOCKED",
            "provider": settings.ai_provider,
            "model": settings.ai_model,
            "readiness_status": diag.status.value,
            "reason": diag.safe_error_message,
            "executed_at": datetime.datetime.now().isoformat(),
        }
        with open("real_inference_smoke_test.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return report

    # Real inference execution through the complete AIAdvisorService
    provider = HuggingFaceProvider()
    db = MagicMock()
    rag = MockRAGRetriever()
    safety = SimpleSafetyValidator()
    builder = AIContextBuilder()
    dash = MagicMock()
    dash.build_dashboard.return_value = _build_smoke_dashboard()
    conv = MagicMock()
    conv.get_recent_history.return_value = []

    def _store_asst(conversation_id, content, metadata=None):
        return MagicMock(id=101, role="assistant", content=content, message_metadata=metadata or {}, created_at=datetime.datetime.now())

    conv.store_assistant_message.side_effect = _store_asst
    now = datetime.datetime.now()
    user_msg = MagicMock(id=100, role="user", content="Query", message_metadata={}, created_at=now)
    conv.store_user_message.return_value = user_msg
    conv.create_user_message.return_value = user_msg
    conv.get_conversation.return_value = MagicMock(id=1, user_id=1)
    conv.touch_conversation.return_value = None

    service = AIAdvisorService(
        db=db,
        llm_provider=provider,
        rag_retriever=rag,
        safety_validator=safety,
        context_builder=builder,
        dashboard_service=dash,
        conversation_service=conv,
    )

    test_query = "What is a Systematic Investment Plan (SIP)?"
    print(f"\nExecuting pipeline query: \"{test_query}\"...", flush=True)

    t0 = time.perf_counter()
    req = SendMessageRequest(message=test_query)
    resp = await service.send_chat_message(user_id=1, conversation_id=1, request=req)
    total_elapsed_ms = (time.perf_counter() - t0) * 1000.0

    meta = resp.assistant_message.message_metadata or {}
    lat_meta = meta.get("latency", {})
    qual_meta = meta.get("quality", {})

    report = {
        "status": "SUCCESS",
        "query": test_query,
        "selected_model": meta.get("model", settings.ai_model),
        "total_ms": round(total_elapsed_ms, 2),
        "provider_network_ms": round(lat_meta.get("provider_network_ms", 0.0), 2),
        "ttft_ms": lat_meta.get("ttft_ms"),
        "generation_ms": round(lat_meta.get("generation_ms", 0.0), 2),
        "prompt_tokens": lat_meta.get("prompt_tokens") or lat_meta.get("estimated_prompt_tokens"),
        "generated_tokens": lat_meta.get("generated_tokens"),
        "tokens_per_second": lat_meta.get("tokens_per_second"),
        "quality_score": qual_meta.get("overall_score"),
        "quality_passed": qual_meta.get("passed"),
        "citations_count": len(resp.sources or []),
        "response_sample": resp.assistant_message.content[:200] + "...",
        "executed_at": datetime.datetime.now().isoformat(),
    }

    print("\n--- Real Inference Smoke Test Complete ---", flush=True)
    print(f"Total Wall Latency: {report['total_ms']}ms", flush=True)
    print(f"Provider Latency:    {report['provider_network_ms']}ms", flush=True)
    print(f"Quality Score:       {report['quality_score']} (Passed: {report['quality_passed']})", flush=True)
    print(f"Response:            {report['response_sample']}", flush=True)

    with open("real_inference_smoke_test.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    asyncio.run(run_real_inference_smoke_test())
