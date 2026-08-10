"""Tests for Financial Engine determinism and service integration."""

from datetime import date
from decimal import Decimal

from app.financial import (
    CashFlowInput,
    ExpenseItemInput,
    IncomeItemInput,
    LoanInput,
    SIPInput,
    calculate_cash_flow,
    calculate_loan,
    calculate_sip,
)
from app.services.financial_service import FinancialService


def test_determinism_cash_flow():
    inp = CashFlowInput(
        incomes=[IncomeItemInput(amount=Decimal("75000.50"), category="Salary")],
        expenses=[ExpenseItemInput(amount=Decimal("35000.25"), category="Housing")],
        reference_date=date(2026, 8, 10),
    )

    res1 = calculate_cash_flow(inp)
    res2 = calculate_cash_flow(inp)

    assert res1.model_dump() == res2.model_dump()
    assert res1.net_cash_flow == Decimal("40000.25")


def test_determinism_loan():
    inp = LoanInput(
        principal=Decimal("250000.00"),
        annual_interest_rate_percent=Decimal("8.50"),
        tenure_months=36,
    )

    res1 = calculate_loan(inp)
    res2 = calculate_loan(inp)

    assert res1.model_dump() == res2.model_dump()


def test_determinism_sip():
    inp = SIPInput(
        monthly_contribution=Decimal("10000.00"),
        expected_annual_return_percent=Decimal("15.00"),
        duration_years=Decimal("5.00"),
    )

    res1 = calculate_sip(inp)
    res2 = calculate_sip(inp)

    assert res1.model_dump() == res2.model_dump()


def test_financial_service_delegation():
    inp = LoanInput(
        principal=Decimal("100000.00"),
        annual_interest_rate_percent=Decimal("12.00"),
        tenure_months=12,
    )
    res = FinancialService.calculate_loan(inp)
    assert res.emi == Decimal("8884.88")
