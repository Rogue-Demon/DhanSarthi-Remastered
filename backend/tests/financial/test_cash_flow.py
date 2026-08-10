"""Tests for Cash Flow calculation module."""

from datetime import date
from decimal import Decimal

import pytest

from app.financial import (
    CashFlowInput,
    ExpenseItemInput,
    IncomeItemInput,
    InvalidFinancialInput,
    calculate_cash_flow,
)


def test_cash_flow_normal():
    incomes = [
        IncomeItemInput(amount=Decimal("50000.00"), category="Salary", source="Job"),
        IncomeItemInput(amount=Decimal("10000.50"), category="Freelance", source="Gig"),
    ]
    expenses = [
        ExpenseItemInput(amount=Decimal("20000.00"), category="Rent"),
        ExpenseItemInput(amount=Decimal("5000.25"), category="Food"),
    ]
    inp = CashFlowInput(incomes=incomes, expenses=expenses, reference_date=date(2026, 8, 10))
    res = calculate_cash_flow(inp)

    assert res.total_income == Decimal("60000.50")
    assert res.total_expenses == Decimal("25000.25")
    assert res.net_cash_flow == Decimal("35000.25")
    assert res.income_by_category == {"Salary": Decimal("50000.00"), "Freelance": Decimal("10000.50")}
    assert res.expense_by_category == {"Rent": Decimal("20000.00"), "Food": Decimal("5000.25")}
    assert res.top_expense_categories == [("Rent", Decimal("20000.00")), ("Food", Decimal("5000.25"))]
    assert res.reference_date == date(2026, 8, 10)


def test_cash_flow_income_equal_expenses():
    incomes = [IncomeItemInput(amount=Decimal("30000"), category="Salary")]
    expenses = [ExpenseItemInput(amount=Decimal("30000"), category="Living")]
    res = calculate_cash_flow(CashFlowInput(incomes=incomes, expenses=expenses))

    assert res.total_income == Decimal("30000")
    assert res.total_expenses == Decimal("30000")
    assert res.net_cash_flow == Decimal("0")


def test_cash_flow_income_less_than_expenses():
    incomes = [IncomeItemInput(amount=Decimal("10000"), category="Stipend")]
    expenses = [ExpenseItemInput(amount=Decimal("15000"), category="Tuition")]
    res = calculate_cash_flow(CashFlowInput(incomes=incomes, expenses=expenses))

    assert res.net_cash_flow == Decimal("-5000")


def test_cash_flow_no_incomes_no_expenses():
    res = calculate_cash_flow(CashFlowInput())
    assert res.total_income == Decimal("0")
    assert res.total_expenses == Decimal("0")
    assert res.net_cash_flow == Decimal("0")
    assert res.top_expense_categories == []


def test_cash_flow_negative_income_raises_error():
    incomes = [IncomeItemInput(amount=Decimal("-100"), category="Error")]
    with pytest.raises(InvalidFinancialInput) as exc_info:
        calculate_cash_flow(CashFlowInput(incomes=incomes))
    assert "Income amount cannot be negative" in str(exc_info.value)


def test_cash_flow_negative_expense_raises_error():
    expenses = [ExpenseItemInput(amount=Decimal("-50"), category="Error")]
    with pytest.raises(InvalidFinancialInput) as exc_info:
        calculate_cash_flow(CashFlowInput(expenses=expenses))
    assert "Expense amount cannot be negative" in str(exc_info.value)
