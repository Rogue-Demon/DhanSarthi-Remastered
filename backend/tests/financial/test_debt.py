"""Tests for Debt analysis module."""

from decimal import Decimal

import pytest

from app.financial import InvalidFinancialInput, LiabilityItemInput, analyze_debt
from app.models.enums import LiabilityType


def test_analyze_debt_normal():
    liabilities = [
        LiabilityItemInput(name="Car Loan", liability_type=LiabilityType.PERSONAL_DEBT, outstanding_balance=Decimal("200000"), monthly_payment=Decimal("10000")),
        LiabilityItemInput(name="Credit Card", liability_type=LiabilityType.CREDIT_CARD, outstanding_balance=Decimal("50000"), monthly_payment=Decimal("5000")),
    ]
    res = analyze_debt(liabilities=liabilities, gross_monthly_income=Decimal("50000"))

    assert res.total_liabilities_balance == Decimal("250000")
    assert res.total_monthly_emi == Decimal("15000")
    assert res.dti_percent == Decimal("30.00")  # 15000 / 50000 * 100


def test_analyze_debt_zero_income():
    liabilities = [
        LiabilityItemInput(name="Loan", liability_type=LiabilityType.PERSONAL_DEBT, outstanding_balance=Decimal("100000"), monthly_payment=Decimal("5000")),
    ]
    res = analyze_debt(liabilities=liabilities, gross_monthly_income=Decimal("0"))

    assert res.total_monthly_emi == Decimal("5000")
    assert res.dti_percent is None


def test_analyze_debt_negative_income_raises_error():
    with pytest.raises(InvalidFinancialInput):
        analyze_debt(liabilities=[], gross_monthly_income=Decimal("-1000"))


def test_analyze_debt_negative_payment_raises_error():
    liabilities = [LiabilityItemInput(name="Bad", liability_type=LiabilityType.OTHER, outstanding_balance=Decimal("100"), monthly_payment=Decimal("-10"))]
    with pytest.raises(InvalidFinancialInput):
        analyze_debt(liabilities=liabilities, gross_monthly_income=Decimal("10000"))
