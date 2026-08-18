"""
Unit and Integration Tests for Phase K: Personalized Financial Intelligence & Advisor Reasoning.
"""

import pytest
from datetime import date
from decimal import Decimal

from app.financial.types import (
    CashFlowResult,
    DebtAnalysisResult,
    FinancialMetricsResult,
    NetWorthResult,
    PortfolioSummaryResult,
    SavingsResult,
)
from app.financial.health_snapshot import build_financial_health_snapshot
from app.financial.signals import evaluate_financial_signals, FinancialSignalType, SignalSeverity
from app.ai.router import IntentRouter, QueryIntent, SubIntent
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.exceptions import AISafetyError
from app.ai.schemas.advisor import AIContext


def test_financial_health_snapshot_complete_data():
    metrics = FinancialMetricsResult(
        cash_flow=CashFlowResult(
            total_income=Decimal("100000.00"),
            total_expenses=Decimal("40000.00"),
            net_cash_flow=Decimal("60000.00"),
            income_by_category={"Salary": Decimal("100000.00")},
            expense_by_category={"Rent": Decimal("40000.00")},
            top_expense_categories=[("Rent", Decimal("40000.00"))],
            reference_date=date(2026, 8, 1),
        ),
        savings=SavingsResult(
            total_income=Decimal("100000.00"),
            total_expenses=Decimal("40000.00"),
            savings=Decimal("60000.00"),
            savings_rate_percent=Decimal("60.0"),
            is_income_zero=False,
            reference_date=date(2026, 8, 1),
        ),
        net_worth=NetWorthResult(
            total_assets=Decimal("500000.00"),
            total_liabilities=Decimal("100000.00"),
            net_worth=Decimal("400000.00"),
            liquid_assets=Decimal("240000.00"),
            illiquid_assets=Decimal("260000.00"),
            assets_by_type={"BANK_BALANCE": Decimal("240000.00")},
            liabilities_by_type={"PERSONAL_LOAN": Decimal("100000.00")},
            reference_date=date(2026, 8, 1),
        ),
        debt=DebtAnalysisResult(
            total_liabilities_balance=Decimal("100000.00"),
            total_monthly_emi=Decimal("15000.00"),
            dti_percent=Decimal("15.0"),
            reference_date=date(2026, 8, 1),
        ),
        emergency_fund_coverage_months=Decimal("6.0"),
        portfolio_summary=PortfolioSummaryResult(
            total_invested=Decimal("100000.00"),
            current_value=Decimal("120000.00"),
            total_gain_loss=Decimal("20000.00"),
            total_return_percentage=Decimal("20.0"),
            allocation_by_type={"MUTUAL_FUND": Decimal("120000.00")},
            allocation_percentages={"MUTUAL_FUND": Decimal("100.0")},
        ),
        reference_date=date(2026, 8, 1),
    )

    snapshot = build_financial_health_snapshot(user_id=1, metrics=metrics)

    assert snapshot.savings.status == "GOOD"
    assert snapshot.savings.savings_rate_percent == Decimal("60.0")
    assert snapshot.liquidity.status == "OPTIMAL"
    assert snapshot.liquidity.coverage_months == Decimal("6.0")
    assert snapshot.debt.status == "HEALTHY"
    assert snapshot.investments.status == "CONCENTRATED"
    assert snapshot.health_score.overall_score is not None
    assert snapshot.health_score.overall_score >= 70


def test_financial_health_snapshot_missing_data():
    empty_metrics = FinancialMetricsResult(reference_date=date(2026, 8, 1))
    snapshot = build_financial_health_snapshot(user_id=1, metrics=empty_metrics)

    assert snapshot.savings.status == "INSUFFICIENT_DATA"
    assert snapshot.expenses.status == "INSUFFICIENT_DATA"
    assert snapshot.debt.status == "INSUFFICIENT_DATA"
    assert snapshot.liquidity.status == "INSUFFICIENT_DATA"
    assert snapshot.health_score.status == "INSUFFICIENT_DATA"
    assert snapshot.health_score.overall_score is None


def test_financial_signals_trigger():
    metrics = FinancialMetricsResult(
        cash_flow=CashFlowResult(
            total_income=Decimal("100000.00"),
            total_expenses=Decimal("85000.00"),
            net_cash_flow=Decimal("15000.00"),
            income_by_category={"Salary": Decimal("100000.00")},
            expense_by_category={"Rent": Decimal("85000.00")},
            top_expense_categories=[("Rent", Decimal("85000.00"))],
            reference_date=date(2026, 8, 1),
        ),
        savings=SavingsResult(
            total_income=Decimal("100000.00"),
            total_expenses=Decimal("85000.00"),
            savings=Decimal("15000.00"),
            savings_rate_percent=Decimal("15.0"),
            is_income_zero=False,
            reference_date=date(2026, 8, 1),
        ),
        debt=DebtAnalysisResult(
            total_liabilities_balance=Decimal("500000.00"),
            total_monthly_emi=Decimal("45000.00"),
            dti_percent=Decimal("45.0"),
            reference_date=date(2026, 8, 1),
        ),
        reference_date=date(2026, 8, 1),
    )

    snapshot = build_financial_health_snapshot(user_id=1, metrics=metrics)
    signals = evaluate_financial_signals(snapshot)

    signal_types = [s.type for s in signals]
    assert FinancialSignalType.HIGH_DEBT_BURDEN in signal_types
    assert FinancialSignalType.HIGH_EXPENSE_RATIO in signal_types


def test_sub_intent_classification():
    router = IntentRouter()

    assert router.classify_sub_intent("How am I doing financially?") == SubIntent.PERSONAL_HEALTH
    assert router.classify_sub_intent("Where am I overspending?") == SubIntent.SPENDING_ANALYSIS
    assert router.classify_sub_intent("Should I focus on debt or investments?") == SubIntent.DEBT_ANALYSIS
    assert router.classify_sub_intent("Am I taking too much investment risk?") == SubIntent.INVESTMENT_ANALYSIS
    assert router.classify_sub_intent("Can I afford my goal?") == SubIntent.GOAL_ANALYSIS
    assert router.classify_sub_intent("Why is my net worth growing slowly?") == SubIntent.NET_WORTH_ANALYSIS


def test_safety_validator_enhanced_rules():
    validator = SimpleSafetyValidator()
    ctx = AIContext(question="Test")

    # Safe advice response
    validator.validate_response(
        "Based on your savings rate of 40%, you have a solid foundation.", ctx
    )

    # Rejects return guarantees
    with pytest.raises(AISafetyError, match="unsafe guarantees"):
        validator.validate_response(
            "This mutual fund will definitely earn you 25% guaranteed returns.", ctx
        )

    # Rejects direct imperative trading commands
    with pytest.raises(AISafetyError, match="impermissible direct trading commands"):
        validator.validate_response(
            "You should sell your stock immediately to avoid losses.", ctx
        )
