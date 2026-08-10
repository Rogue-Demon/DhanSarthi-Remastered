"""Tests for Loans calculation and affordability module."""

from decimal import Decimal

import pytest

from app.financial import (
    InvalidFinancialInput,
    InvalidLoanParameters,
    LoanAffordabilityInput,
    LoanInput,
    analyze_loan_affordability,
    calculate_loan,
)


def test_loan_emi_standard():
    # Principal: 100,000, Rate: 12% p.a., Tenure: 12 months
    # Formula monthly rate r = 0.01.
    # EMI = 100000 * 0.01 * (1.01^12) / ((1.01^12) - 1) = 8884.8788... -> 8884.88
    inp = LoanInput(
        principal=Decimal("100000.00"),
        annual_interest_rate_percent=Decimal("12.00"),
        tenure_months=12,
    )
    res = calculate_loan(inp, include_amortization=True)

    assert res.emi == Decimal("8884.88")
    assert res.total_repayment == Decimal("106618.56")
    assert res.total_interest == Decimal("6618.56")
    assert len(res.amortization_schedule) == 12

    # Schedule assertions
    first = res.amortization_schedule[0]
    assert first.payment_number == 1
    assert first.opening_balance == Decimal("100000.00")
    assert first.interest_component == Decimal("1000.00")  # 100,000 * 0.01

    last = res.amortization_schedule[-1]
    assert last.payment_number == 12
    assert last.closing_balance == Decimal("0.00")


def test_loan_zero_interest():
    inp = LoanInput(
        principal=Decimal("60000.00"),
        annual_interest_rate_percent=Decimal("0.00"),
        tenure_months=12,
    )
    res = calculate_loan(inp)

    assert res.emi == Decimal("5000.00")
    assert res.total_repayment == Decimal("60000.00")
    assert res.total_interest == Decimal("0.00")
    assert res.amortization_schedule[-1].closing_balance == Decimal("0.00")


def test_loan_invalid_parameters():
    # Non-positive principal
    with pytest.raises(InvalidLoanParameters):
        calculate_loan(LoanInput(principal=Decimal("0"), annual_interest_rate_percent=Decimal("10"), tenure_months=12))

    # Negative rate
    with pytest.raises(InvalidLoanParameters):
        calculate_loan(LoanInput(principal=Decimal("10000"), annual_interest_rate_percent=Decimal("-5"), tenure_months=12))

    # Non-positive tenure
    with pytest.raises(InvalidLoanParameters):
        calculate_loan(LoanInput(principal=Decimal("10000"), annual_interest_rate_percent=Decimal("10"), tenure_months=0))


def test_loan_affordability_analysis():
    proposed = LoanInput(
        principal=Decimal("500000.00"),
        annual_interest_rate_percent=Decimal("10.00"),
        tenure_months=60,
    )
    aff_input = LoanAffordabilityInput(
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("30000.00"),
        existing_monthly_emi=Decimal("10000.00"),
        proposed_loan=proposed,
        liquid_savings=Decimal("100000.00"),
    )
    res = analyze_loan_affordability(aff_input)

    assert res.total_monthly_income == Decimal("80000.00")
    assert res.existing_monthly_debt == Decimal("10000.00")
    assert res.current_dti_percent == Decimal("12.50")  # 10000 / 80000 * 100
    assert res.proposed_emi > Decimal("0")
    assert res.proposed_dti_percent > res.current_dti_percent
    assert res.net_monthly_cash_flow_after_loan == (
        Decimal("80000.00") - Decimal("30000.00") - res.existing_monthly_debt - res.proposed_emi
    )


def test_loan_affordability_negative_income_raises_error():
    proposed = LoanInput(principal=Decimal("100000"), annual_interest_rate_percent=Decimal("10"), tenure_months=12)
    with pytest.raises(InvalidFinancialInput):
        analyze_loan_affordability(
            LoanAffordabilityInput(
                monthly_income=Decimal("-5000"),
                monthly_expenses=Decimal("1000"),
                existing_monthly_emi=Decimal("0"),
                proposed_loan=proposed,
            )
        )
