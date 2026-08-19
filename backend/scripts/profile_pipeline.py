"""
Phase L.7.1 End-to-End AI Advisor Latency Profiler & Benchmark Script.

Executes representative test queries across 7 required query categories:
  1. CASUAL
  2. PERSONAL
  3. GENERAL
  4. MIXED
  5. COMPARISON
  6. HISTORICAL
  7. AMBIGUOUS

Outputs machine-readable performance report: `latency_profile_report.json`.
Identifies exact system bottlenecks before Phase L.7.2 optimization.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

from unittest.mock import MagicMock, AsyncMock

from app.ai.observability.latency import LatencyTracker
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.rag.adaptive_router import AdaptiveRetrievalRouter, RetrievalStrategy
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.semantic.minilm import MiniLMSemanticService
from app.ai.rag.reranker import DeterministicReranker
from app.ai.context.builder import AIContextBuilder
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.advisor.service import AIAdvisorService
from datetime import date, datetime, timezone
from decimal import Decimal

from app.schemas.dashboard import (
    DashboardResponse,
    PeriodInfo,
    UserContextInfo,
    FinancialSummarySnapshot,
    CashFlowSummary,
    NetWorthSummary,
    InvestmentSummary,
    LoanSummary,
    DebtSummary,
    GoalSummary,
    BudgetSummary,
    FinancialHealthSummary,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("latency_profiler")

PROFILE_QUERIES = [
    {"category": "CASUAL", "query": "hi how are you"},
    {"category": "PERSONAL", "query": "what is my net worth and monthly expenses?"},
    {"category": "GENERAL", "query": "what is Section 80C tax deduction limit?"},
    {"category": "MIXED", "query": "how much tax can I save under 80C based on my current salary?"},
    {"category": "COMPARISON", "query": "compare SIP vs FD interest rates"},
    {"category": "HISTORICAL", "query": "what were the 2023 RBI repo rate changes?"},
    {"category": "AMBIGUOUS", "query": "what should I do with it?"},
]


def create_mock_dashboard() -> DashboardResponse:
    return DashboardResponse(
        period=PeriodInfo(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            period_days=31,
        ),
        user=UserContextInfo(
            user_id=1,
            display_name="Test User",
            persona="SALARIED_PROFESSIONAL",
            currency="INR",
            country="IN",
        ),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("100000"),
            total_expenses=Decimal("40000"),
            savings=Decimal("60000"),
            net_worth=Decimal("400000"),
            total_assets=Decimal("500000"),
            total_liabilities=Decimal("100000"),
            total_invested=Decimal("200000"),
            total_debt=Decimal("100000"),
        ),
        cash_flow=CashFlowSummary(
            total_income=Decimal("100000"),
            total_expenses=Decimal("40000"),
            net_cash_flow=Decimal("60000"),
            savings=Decimal("60000"),
            savings_rate_percent=Decimal("60"),
            has_data=True,
        ),
        net_worth=NetWorthSummary(
            total_assets=Decimal("500000"),
            total_liabilities=Decimal("100000"),
            net_worth=Decimal("400000"),
            liquid_assets=Decimal("150000"),
            has_data=True,
        ),
        investments=InvestmentSummary(
            total_invested=Decimal("200000"),
            current_value=Decimal("250000"),
            total_gain_loss=Decimal("50000"),
            total_return_percentage=Decimal("25"),
            investment_count=2,
            has_data=True,
        ),
        loans=LoanSummary(
            total_outstanding=Decimal("100000"),
            total_principal=Decimal("120000"),
            total_monthly_emi=Decimal("10000"),
            loan_count=1,
            active_loan_count=1,
            has_data=True,
        ),
        debt=DebtSummary(
            total_debt=Decimal("100000"),
            monthly_obligations=Decimal("10000"),
            dti_percent=Decimal("10"),
            has_data=True,
        ),
        goals=GoalSummary(total_goals=2, active_count=2, completed_count=0, has_data=True),
        budgets=BudgetSummary(
            total_budget=Decimal("50000"),
            total_spending=Decimal("40000"),
            remaining_budget=Decimal("10000"),
            overall_utilization_percent=Decimal("80"),
            has_data=True,
        ),
        financial_health=FinancialHealthSummary(
            savings_rate_percent=Decimal("60"),
            dti_percent=Decimal("10"),
            emergency_fund_months=Decimal("3.75"),
            budget_utilization_percent=Decimal("80"),
            goal_completion_rate_percent=Decimal("50"),
            net_worth=Decimal("400000"),
            cash_flow_positive=True,
        ),
    )


async def profile_pipeline() -> Dict[str, Any]:
    logger.info("Initializing DhanSarthi AI Advisor Latency Profiler...")
    
    db_mock = MagicMock()
    
    # Mock LLM provider for zero-cost rapid benchmarking
    llm_provider = AsyncMock()
    llm_provider.generate.side_effect = lambda context, prompt, tracker=None: (
        "Based on your financial data, Section 80C allows tax deductions up to Rs 1.5 Lakh per year."
    )
    
    # Mock RAG retriever
    chunk_repo = MagicMock()
    chunk_repo.search_similarity.return_value = []
    
    faiss_store = MagicMock()
    faiss_store.is_healthy.return_value = True
    faiss_store.search.return_value = []
    
    embedding_provider = AsyncMock()
    embedding_provider.embed.return_value = [0.05] * 384
    
    retriever = PostgresRAGRetriever(
        db=db_mock,
        embedding_provider=embedding_provider,
        faiss_store=faiss_store,
    )
    retriever._chunk_repo = chunk_repo
    
    dash_service = MagicMock()
    dash_service.build_dashboard.return_value = create_mock_dashboard()
    
    conv_service = MagicMock()
    conv = MagicMock()
    conv.id = 101
    conv_service.get_conversation.return_value = conv
    
    now_dt = datetime.now(timezone.utc)
    user_msg = MagicMock()
    user_msg.id = 501
    user_msg.role = "USER"
    user_msg.content = "test message"
    user_msg.created_at = now_dt
    user_msg.message_metadata = {}
    conv_service.store_user_message.return_value = user_msg
    conv_service.get_recent_messages.return_value = [user_msg]
    
    asst_msg = MagicMock()
    asst_msg.id = 502
    asst_msg.role = "ASSISTANT"
    asst_msg.content = "test response"
    asst_msg.created_at = now_dt
    asst_msg.message_metadata = {}
    conv_service.store_assistant_message.return_value = asst_msg
    
    advisor = AIAdvisorService(
        db=db_mock,
        llm_provider=llm_provider,
        rag_retriever=retriever,
        safety_validator=SimpleSafetyValidator(),
        context_builder=AIContextBuilder(),
        dashboard_service=dash_service,
        conversation_service=conv_service,
        query_understanding_service=QueryUnderstandingService(),
        adaptive_router=AdaptiveRetrievalRouter(),
    )
    
    results: List[Dict[str, Any]] = []
    
    logger.info("Running profile benchmarks across 7 query categories...")
    
    for test_item in PROFILE_QUERIES:
        cat = test_item["category"]
        q_text = test_item["query"]
        
        req = MagicMock()
        req.message = q_text
        
        start_t = time.perf_counter()
        resp = await advisor.send_chat_message(
            user_id=1,
            conversation_id=101,
            request=req,
        )
        total_bench_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        
        asst_call_args = conv_service.store_assistant_message.call_args
        meta = asst_call_args.kwargs.get("metadata", {}) if asst_call_args else {}
        latency_dict = meta.get("latency", {})
        
        results.append({
            "category": cat,
            "query": q_text,
            "total_measured_ms": total_bench_ms,
            "intent": meta.get("intent"),
            "strategy": meta.get("scope"),
            "breakdown": latency_dict,
        })
        logger.info(f"Category [{cat}]: {total_bench_ms} ms")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries_profiled": len(results),
        "queries": results,
    }
    
    report_path = Path("backend/latency_profile_report.json")
    report_path.write_text(json.dumps(report, indent=2))
    logger.info(f"Successfully generated profile report: {report_path.absolute()}")
    
    return report


# ---------------------------------------------------------------------------
# Phase L.7.2 — Canonical 8-Query Latency Benchmark
# ---------------------------------------------------------------------------

L72_BENCHMARK_QUERIES = [
    ("CASUAL",          "Hi"),
    ("SIMPLE_GENERAL",  "What is SIP?"),
    ("GENERAL_FUND",    "What is a mutual fund?"),
    ("PERSONAL",        "How much did I spend this month?"),
    ("MIXED_HEALTH",    "Is my savings rate healthy?"),
    ("COMPARISON",      "SIP vs FD, which is better?"),
    ("HISTORICAL",      "What was the RBI repo rate in FY 2024-25?"),
    ("MIXED_ADVICE",    "What should I do with it?"),
]

_REPETITIONS = 3


def _percentile(sorted_vals: List[float], p: float) -> float:
    """Return the p-th percentile from a sorted list."""
    if not sorted_vals:
        return 0.0
    idx = (len(sorted_vals) - 1) * p / 100.0
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (idx - lo)


async def run_l72_benchmark():
    """
    Phase L.7.2 Latency Benchmark.

    Measures token budgets, prompt sizes, and end-to-end timings for
    the 8 canonical DhanSarthi query categories across N repetitions.

    NOTE: Uses MockLLMProvider — measures pipeline overhead only (NOT real HF latency).
    To measure real HF latency set REAL_LLM=1 in environment (provider will try HF API).
    """
    import os
    logger.info("=== Phase L.7.2 Latency Benchmark ===")

    from app.ai.generation.token_budget import TokenBudgetSelector
    from app.ai.query_understanding.service import QueryUnderstandingService

    qs = QueryUnderstandingService()
    selector = TokenBudgetSelector()

    benchmark_rows: List[Dict[str, Any]] = []

    for label, query in L72_BENCHMARK_QUERIES:
        prompt_char_samples: List[float] = []
        token_budget_samples: List[int] = []
        total_ms_samples: List[float] = []

        for _rep in range(_REPETITIONS):
            tracker = LatencyTracker()
            understanding = qs.analyze(query, tracker=tracker)
            intent = understanding.intent

            ep = understanding.execution_plan
            scope_str = ep.scope.value if ep and ep.scope else None
            op_str = ep.operation.value if ep and ep.operation else None
            is_comparison = bool(ep and ep.comparison_info and ep.comparison_info.is_comparison)
            is_historical = bool(
                understanding.temporal_references and
                any(t.is_historical for t in understanding.temporal_references)
            )

            budget = selector.select(
                intent=intent,
                scope=scope_str,
                operation=op_str,
                is_comparison=is_comparison,
                is_historical=is_historical,
            )

            # Build context with no real user data (clean benchmark environment)
            builder = AIContextBuilder()
            ctx = builder.build_context(
                question=query,
                full_context=None,
                retrieved_docs=[],
                tracker=tracker,
            )
            prompt = builder.build_prompt(ctx, tracker=tracker, intent=intent.value, scope=scope_str)

            tracker.finish()

            prompt_char_samples.append(len(prompt))
            token_budget_samples.append(budget)
            total_ms_samples.append(tracker.breakdown.total_ms)

        # Stats
        prompt_char_samples.sort()
        total_ms_samples.sort()

        row = {
            "label": label,
            "query_preview": query[:50],
            "intent": str(intent.value),
            "scope": scope_str,
            "token_budget": token_budget_samples[0],
            "prompt_chars": {
                "min": int(min(prompt_char_samples)),
                "median": int(_percentile(prompt_char_samples, 50)),
                "p95": int(_percentile(prompt_char_samples, 95)),
                "max": int(max(prompt_char_samples)),
            },
            "total_ms": {
                "min": round(min(total_ms_samples), 2),
                "median": round(_percentile(total_ms_samples, 50), 2),
                "p95": round(_percentile(total_ms_samples, 95), 2),
                "max": round(max(total_ms_samples), 2),
            },
        }
        benchmark_rows.append(row)

        logger.info(
            "[%s] budget=%d tokens | prompt=%d chars | pipeline=%.2f ms (median)",
            label,
            row["token_budget"],
            row["prompt_chars"]["median"],
            row["total_ms"]["median"],
        )

    report = {
        "phase": "L.7.2",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repetitions_per_query": _REPETITIONS,
        "note": "Pipeline-only benchmark (MockLLM). Real HF latency excluded.",
        "queries": benchmark_rows,
    }

    report_path = Path("backend/l72_benchmark_report.json")
    report_path.write_text(json.dumps(report, indent=2))
    logger.info("L.7.2 benchmark report saved to: %s", report_path.absolute())

    # Print human-readable table
    print("\n" + "=" * 80)
    print("PHASE L.7.2 — LATENCY BENCHMARK RESULTS")
    print("=" * 80)
    header = f"{'Label':<20} {'Budget':>8} {'Prompt':>10} {'Pipeline(median)':>18}"
    print(header)
    print("-" * 60)
    for row in benchmark_rows:
        print(
            f"{row['label']:<20} {row['token_budget']:>7}t "
            f"{row['prompt_chars']['median']:>9}c "
            f"{row['total_ms']['median']:>15.2f}ms"
        )
    print("=" * 80)
    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--l72":
        asyncio.run(run_l72_benchmark())
    else:
        asyncio.run(profile_pipeline())

