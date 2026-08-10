"""Tests for Financial Health module."""

from decimal import Decimal

import pytest

from app.financial import (
    AssetItemInput,
    CashFlowInput,
    ExpenseItemInput,
    FinancialMetricsInput,
    IncomeItemInput,
    InvalidFinancialInput,
    LiabilityItemInput,
    NetWorthInput,
    calculate_emergency_fund_coverage,
    calculate_financial_metrics,
)
from app.models.enums import AssetType, LiabilityType


def test_emergency_fund_coverage():
    # Liquid savings = 150,000, Monthly essential expenses = 25,000 -> 6.00 months
    coverage = calculate_emergency_fund_coverage(Decimal("150000.00"), Decimal("25000.00"))
    assert coverage == Decimal("6.00")


def test_emergency_fund_zero_essential_expenses():
    coverage = calculate_emergency_fund_coverage(Decimal("100000.00"), Decimal("0.00"))
    assert coverage is None


def test_emergency_fund_negative_savings_raises_error():
    with pytest.raises(InvalidFinancialInput):
        calculate_emergency_fund_coverage(Decimal("-100"), Decimal("1000"))


def test_financial_metrics_consolidation():
    cf = CashFlowInput(
        incomes=[IncomeItemInput(amount=Decimal("100000"), category="Salary")],
        expenses=[ExpenseItemInput(amount=Decimal("40000"), category="Rent")],
    )
    nw = NetWorthInput(
        assets=[AssetItemInput(name="Cash", asset_type=AssetType.CASH, current_value=Decimal("200000"), is_liquid=True)],
        liabilities=[LiabilityItemInput(name="Loan", liability_type=LiabilityType.PERSONAL_DEBT, outstanding_balance=Decimal("50000"), monthly_payment=Decimal("5000"))],
    )
    inp = FinancialMetricsInput(
        cash_flow_input=cf,
        net_worth_input=nw,
        monthly_essential_expenses=Decimal("25000"),
    )
    res = calculate_financial_metrics(inp)

    assert res.cash_flow.total_income == Decimal("100000")
    assert res.savings.savings_rate_percent == Decimal("60.00")
    assert res.net_worth.net_worth == Decimal("150000")
    assert res.debt.dti_percent == Decimal("5.00")  # 5000 / 100000 * 100
    assert res.emergency_fund_coverage_months == Decimal("8.00")  # 200,000 / 25,000
