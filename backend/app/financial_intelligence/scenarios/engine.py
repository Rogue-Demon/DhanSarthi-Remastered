"""
Deterministic financial scenario simulators and loan affordability engine.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.financial_intelligence.schemas import LoanScenarioResult, GenericScenarioResult


def calculate_emi(principal: Decimal, annual_rate_percent: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate monthly EMI using standard reducing-balance amortizing formula.
    """
    if principal <= Decimal("0") or tenure_months <= 0:
        return Decimal("0")
        
    if annual_rate_percent <= Decimal("0"):
        return (principal / Decimal(tenure_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Monthly interest rate
    r = annual_rate_percent / Decimal("12") / Decimal("100")
    n = tenure_months

    # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    # Using floats for power calculation to avoid Decimal limitation on non-integer exponentiation
    try:
        power = Decimal(str(math_pow(1 + float(r), n)))
        emi = principal * r * power / (power - 1)
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        # Fallback to simple calculation
        return (principal / Decimal(tenure_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def math_pow(base: float, exp: float) -> float:
    import math
    return math.pow(base, exp)


def run_loan_scenario(
    principal: Decimal,
    annual_interest_rate_percent: Decimal,
    tenure_months: int,
    monthly_income: Decimal,
    existing_monthly_debt: Decimal,
    essential_expenses: Decimal,
) -> LoanScenarioResult:
    """
    Evaluate loan affordability and compute post-loan DTI, cash flow, and risk indicators.
    """
    # 1. Calculate EMI
    emi = calculate_emi(principal, annual_interest_rate_percent, tenure_months)
    total_repayment = emi * Decimal(tenure_months)
    total_interest = total_repayment - principal

    # 2. Post-loan Debt-to-Income
    new_monthly_debt = existing_monthly_debt + emi
    if monthly_income > Decimal("0"):
        post_loan_dti = ((new_monthly_debt / monthly_income) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        post_loan_dti = None

    # 3. Post-loan monthly cash flow
    # post_loan_surplus = income - expenses - existing_debt - emi
    total_obligations = essential_expenses + existing_monthly_debt + emi
    post_loan_surplus = monthly_income - total_obligations

    if post_loan_surplus > 0:
        post_loan_cash_flow_status = "POSITIVE"
    elif post_loan_surplus == Decimal("0"):
        post_loan_cash_flow_status = "BREAK_EVEN"
    else:
        post_loan_cash_flow_status = "NEGATIVE"

    # 4. Evaluate Risk Flags
    risk_flags: List[str] = []
    
    if monthly_income == Decimal("0"):
        risk_flags.append("INSUFFICIENT_DATA")
    else:
        high_threshold = Decimal(str(settings.dti_threshold_high))
        if post_loan_dti and post_loan_dti > high_threshold:
            risk_flags.append("HIGH_POST_LOAN_DTI")
            
        if post_loan_surplus < (monthly_income * Decimal("0.10")):
            risk_flags.append("LOW_POST_LOAN_SURPLUS")

    if post_loan_surplus < Decimal("0"):
        risk_flags.append("NEGATIVE_POST_LOAN_CASH_FLOW")

    if total_interest > principal:
        risk_flags.append("HIGH_TOTAL_INTEREST")

    return LoanScenarioResult(
        emi=emi,
        total_repayment=total_repayment,
        total_interest=total_interest,
        post_loan_dti=post_loan_dti,
        post_loan_surplus=post_loan_surplus,
        post_loan_cash_flow_status=post_loan_cash_flow_status,
        risk_flags=risk_flags,
        assumptions={
            "interest_compounding": "Monthly reducing balance",
            "annual_interest_rate_percent": float(annual_interest_rate_percent),
            "tenure_months": tenure_months,
        },
        limitations="This simulation is for decision support only and does not guarantee loan approval or lock rates.",
    )


def run_savings_scenario(
    base_expenses: Decimal,
    expense_reduction: Decimal,
    base_income: Decimal,
) -> GenericScenarioResult:
    """
    Project the impact of expense reductions on the monthly surplus.
    """
    base_surplus = base_income - base_expenses
    scenario_expenses = base_expenses - expense_reduction
    scenario_surplus = base_income - scenario_expenses
    diff = scenario_surplus - base_surplus

    return GenericScenarioResult(
        base_value=base_surplus,
        scenario_value=scenario_surplus,
        difference=diff,
        assumptions={"monthly_expense_reduction": float(expense_reduction)},
        limitations="Assumes income remains constant and expense reductions are sustained monthly.",
    )


def run_investment_scenario(
    monthly_contribution: Decimal,
    expected_annual_return_percent: Decimal,
    duration_years: Decimal,
) -> GenericScenarioResult:
    """
    Project compound Systematic Investment Plan (SIP) growth.
    """
    # M * [ (1 + i)^n - 1 ] / i * (1 + i)
    r = expected_annual_return_percent / Decimal("100")
    months = Decimal(str(int(duration_years * Decimal("12"))))
    
    total_invested = monthly_contribution * months

    if r <= Decimal("0") or monthly_contribution <= Decimal("0"):
        future_value = total_invested
    else:
        i = r / Decimal("12")
        try:
            power = Decimal(str(math_pow(1 + float(i), float(months))))
            future_value = monthly_contribution * ((power - 1) / i) * (1 + i)
        except Exception:
            future_value = total_invested

    future_value = future_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gains = future_value - total_invested

    return GenericScenarioResult(
        base_value=total_invested,
        scenario_value=future_value,
        difference=gains,
        assumptions={
            "expected_annual_return_percent": float(expected_annual_return_percent),
            "duration_years": float(duration_years),
            "compounding": "Monthly",
        },
        limitations="Projections are illustrative and do not represent guaranteed future market returns.",
    )


def run_goal_scenario(
    target_amount: Decimal,
    current_amount: Decimal,
    months_remaining: int,
    proposed_monthly_contribution: Decimal,
) -> GenericScenarioResult:
    """
    Project goal completion details given a proposed monthly contribution.
    """
    remaining_balance = target_amount - current_amount
    total_proposed_savings = proposed_monthly_contribution * Decimal(months_remaining)
    shortfall = remaining_balance - total_proposed_savings
    
    # We report the shortfall / surplus relative to the remaining balance target
    # base_value is the remaining balance target.
    # scenario_value is the projected shortfall/surplus (negative is shortfall, positive is surplus).
    return GenericScenarioResult(
        base_value=remaining_balance,
        scenario_value=total_proposed_savings,
        difference=total_proposed_savings - remaining_balance,
        assumptions={
            "months_remaining": months_remaining,
            "proposed_monthly_contribution": float(proposed_monthly_contribution),
        },
        limitations="Assumes zero interest growth and constant monthly savings rate.",
    )
