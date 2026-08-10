"""Tests for Savings calculation module."""

from decimal import Decimal

import pytest

from app.financial import InvalidFinancialInput, calculate_savings


def test_savings_normal():
    res = calculate_savings(Decimal("100000.00"), Decimal("60000.00"))
    assert res.total_income == Decimal("100000.00")
    assert res.total_expenses == Decimal("60000.00")
    assert res.savings == Decimal("40000.00")
    assert res.savings_rate_percent == Decimal("40.00")
    assert res.is_income_zero is False


def test_savings_zero_income():
    res = calculate_savings(Decimal("0.00"), Decimal("5000.00"))
    assert res.savings == Decimal("-5000.00")
    assert res.savings_rate_percent is None
    assert res.is_income_zero is True


def test_savings_equal_income_expenses():
    res = calculate_savings(Decimal("50000.00"), Decimal("50000.00"))
    assert res.savings == Decimal("0.00")
    assert res.savings_rate_percent == Decimal("0.00")
    assert res.is_income_zero is False


def test_savings_negative_income_raises_exception():
    with pytest.raises(InvalidFinancialInput):
        calculate_savings(Decimal("-100"), Decimal("50"))


def test_savings_negative_expense_raises_exception():
    with pytest.raises(InvalidFinancialInput):
        calculate_savings(Decimal("100"), Decimal("-50"))


def test_savings_rounding_precision():
    res = calculate_savings(Decimal("33333.33"), Decimal("10000.00"))
    # (23333.33 / 33333.33) * 100 = 69.99999... -> 70.00
    assert res.savings_rate_percent == Decimal("70.00")
