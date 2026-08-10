"""
DhanSarthi Financial Engine — Loan & Affordability Module.

Provides deterministic loan EMI, interest breakdown, complete amortization
schedule generation, and loan affordability metrics.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

from app.financial.exceptions import InvalidFinancialInput, InvalidLoanParameters
from app.financial.types import (
    AmortizationScheduleEntry,
    LoanAffordabilityInput,
    LoanAffordabilityResult,
    LoanCalculationResult,
    LoanInput,
)


def calculate_loan(
    input_data: LoanInput, include_amortization: bool = True
) -> LoanCalculationResult:
    """
    Calculate loan EMI, total repayment, total interest, and optional amortization schedule.

    Formulas:
        If rate == 0:
            EMI = Principal / Tenure
        Else:
            r = (Annual Rate / 100) / 12
            EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

    Args:
        input_data: LoanInput payload.
        include_amortization: Whether to build full schedule (default True).

    Returns:
        LoanCalculationResult: Structured loan metrics and schedule.

    Raises:
        InvalidLoanParameters: If principal <= 0, tenure <= 0, or rate < 0.
    """
    p = input_data.principal
    rate_pct = input_data.annual_interest_rate_percent
    n = input_data.tenure_months

    if p <= Decimal("0"):
        raise InvalidLoanParameters(
            f"Loan principal must be strictly positive: {p}",
            details={"principal": str(p)},
        )
    if rate_pct < Decimal("0"):
        raise InvalidLoanParameters(
            f"Annual interest rate cannot be negative: {rate_pct}",
            details={"annual_interest_rate_percent": str(rate_pct)},
        )
    if n <= 0:
        raise InvalidLoanParameters(
            f"Tenure in months must be strictly positive: {n}",
            details={"tenure_months": n},
        )

    if rate_pct == Decimal("0"):
        r = Decimal("0")
        raw_emi = p / Decimal(n)
    else:
        r = (rate_pct / Decimal("100")) / Decimal("12")
        factor = (Decimal("1") + r) ** n
        raw_emi = p * r * factor / (factor - Decimal("1"))

    emi = raw_emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_repayment = emi * Decimal(n)
    total_interest = total_repayment - p

    schedule: List[AmortizationScheduleEntry] | None = None
    if include_amortization:
        schedule = []
        opening = p
        for k in range(1, n + 1):
            if rate_pct > Decimal("0"):
                interest_comp = (opening * r).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                interest_comp = Decimal("0")

            if k == n:
                # Adjust final month principal component to absorb rounding residuals
                principal_comp = opening
                closing = Decimal("0")
                month_emi = principal_comp + interest_comp
            else:
                principal_comp = emi - interest_comp
                closing = opening - principal_comp
                month_emi = emi

            schedule.append(
                AmortizationScheduleEntry(
                    payment_number=k,
                    opening_balance=opening,
                    emi=month_emi,
                    principal_component=principal_comp,
                    interest_component=interest_comp,
                    closing_balance=closing,
                )
            )
            opening = closing

    assumptions: Dict[str, Any] = {
        "principal": str(p),
        "annual_interest_rate_percent": str(rate_pct),
        "tenure_months": n,
        "payment_frequency": input_data.payment_frequency,
        "is_zero_interest": rate_pct == Decimal("0"),
    }

    return LoanCalculationResult(
        principal=p,
        annual_interest_rate_percent=rate_pct,
        tenure_months=n,
        emi=emi,
        total_repayment=total_repayment,
        total_interest=total_interest,
        amortization_schedule=schedule,
        assumptions=assumptions,
    )


def analyze_loan_affordability(
    input_data: LoanAffordabilityInput,
) -> LoanAffordabilityResult:
    """
    Evaluate deterministic loan affordability metrics for a proposed loan.

    Args:
        input_data: LoanAffordabilityInput containing income, expenses, current debt, and proposed loan.

    Returns:
        LoanAffordabilityResult: Structured numerical facts regarding loan affordability.

    Raises:
        InvalidFinancialInput: If income, expenses, or existing debt are negative.
    """
    if input_data.monthly_income < Decimal("0"):
        raise InvalidFinancialInput(
            f"Monthly income cannot be negative: {input_data.monthly_income}",
            details={"monthly_income": str(input_data.monthly_income)},
        )
    if input_data.monthly_expenses < Decimal("0"):
        raise InvalidFinancialInput(
            f"Monthly expenses cannot be negative: {input_data.monthly_expenses}",
            details={"monthly_expenses": str(input_data.monthly_expenses)},
        )
    if input_data.existing_monthly_emi < Decimal("0"):
        raise InvalidFinancialInput(
            f"Existing monthly EMI cannot be negative: {input_data.existing_monthly_emi}",
            details={"existing_monthly_emi": str(input_data.existing_monthly_emi)},
        )

    loan_res = calculate_loan(input_data.proposed_loan, include_amortization=False)
    proposed_emi = loan_res.emi

    income = input_data.monthly_income
    existing_debt = input_data.existing_monthly_emi
    expenses = input_data.monthly_expenses
    new_total_debt = existing_debt + proposed_emi

    if income > Decimal("0"):
        raw_current_dti = (existing_debt / income) * Decimal("100")
        current_dti_percent = raw_current_dti.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        raw_proposed_dti = (new_total_debt / income) * Decimal("100")
        proposed_dti_percent = raw_proposed_dti.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        current_dti_percent = None
        proposed_dti_percent = None

    net_post_loan_cash_flow = income - expenses - new_total_debt

    metrics: Dict[str, Any] = {
        "monthly_income": str(income),
        "monthly_expenses": str(expenses),
        "existing_monthly_debt": str(existing_debt),
        "proposed_emi": str(proposed_emi),
        "new_total_monthly_debt": str(new_total_debt),
        "net_monthly_cash_flow_after_loan": str(net_post_loan_cash_flow),
        "liquid_savings": str(input_data.liquid_savings) if input_data.liquid_savings is not None else None,
    }

    return LoanAffordabilityResult(
        proposed_emi=proposed_emi,
        total_monthly_income=income,
        existing_monthly_debt=existing_debt,
        new_total_monthly_debt=new_total_debt,
        current_dti_percent=current_dti_percent,
        proposed_dti_percent=proposed_dti_percent,
        net_monthly_cash_flow_after_loan=net_post_loan_cash_flow,
        metrics=metrics,
    )
