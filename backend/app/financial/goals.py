"""
DhanSarthi Financial Engine — Goal Analysis Module.

Provides deterministic analysis of user financial goals, calculating target progress,
remaining horizon, required monthly contributions, and shortfalls.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import GoalAnalysisResult, GoalInput


def analyze_goal(input_data: GoalInput) -> GoalAnalysisResult:
    """
    Analyze goal progress and compute required monthly contribution to reach target.

    Args:
        input_data: GoalInput payload.

    Returns:
        GoalAnalysisResult: Structured goal metrics and required contribution.

    Raises:
        InvalidFinancialInput: If target_amount <= 0 or current_amount < 0.
    """
    ref_date = input_data.reference_date or date.today()
    target_date = input_data.target_date

    target_amt = input_data.target_amount
    curr_amt = input_data.current_amount
    rate_pct = input_data.expected_annual_return_percent

    if target_amt <= Decimal("0"):
        raise InvalidFinancialInput(
            f"Goal target amount must be strictly positive: {target_amt}",
            details={"target_amount": str(target_amt)},
        )
    if curr_amt < Decimal("0"):
        raise InvalidFinancialInput(
            f"Current goal amount cannot be negative: {curr_amt}",
            details={"current_amount": str(curr_amt)},
        )
    if rate_pct < Decimal("0"):
        raise InvalidFinancialInput(
            f"Expected annual return rate cannot be negative: {rate_pct}",
            details={"expected_annual_return_percent": str(rate_pct)},
        )

    remaining_amt = max(Decimal("0"), target_amt - curr_amt)
    is_completed = curr_amt >= target_amt

    raw_comp = (curr_amt / target_amt) * Decimal("100")
    completion_percentage = min(Decimal("100.00"), raw_comp).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Calculate time remaining in calendar months
    months_diff = (target_date.year - ref_date.year) * 12 + (target_date.month - ref_date.month)
    if target_date.day < ref_date.day:
        months_diff -= 1
    time_remaining_months = max(0, months_diff)

    required_monthly_contrib: Decimal | None = None

    if is_completed or remaining_amt == Decimal("0"):
        required_monthly_contrib = Decimal("0")
    elif time_remaining_months == 0:
        required_monthly_contrib = None  # Target date has arrived or passed
    else:
        n = time_remaining_months
        if rate_pct == Decimal("0"):
            required_monthly_contrib = (remaining_amt / Decimal(n)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            r = (rate_pct / Decimal("100")) / Decimal("12")
            factor = (Decimal("1") + r) ** n
            fv_current = curr_amt * factor
            net_needed = target_amt - fv_current
            if net_needed <= Decimal("0"):
                required_monthly_contrib = Decimal("0")
            else:
                annuity_factor = ((factor - Decimal("1")) / r) * (Decimal("1") + r)
                raw_req = net_needed / annuity_factor
                required_monthly_contrib = raw_req.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

    assumptions: Dict[str, Any] = {
        "title": input_data.title,
        "target_amount": str(target_amt),
        "current_amount": str(curr_amt),
        "target_date": target_date.isoformat(),
        "reference_date": ref_date.isoformat(),
        "expected_annual_return_percent": str(rate_pct),
        "time_remaining_months": time_remaining_months,
    }

    return GoalAnalysisResult(
        title=input_data.title,
        target_amount=target_amt,
        current_amount=curr_amt,
        remaining_amount=remaining_amt,
        time_remaining_months=time_remaining_months,
        completion_percentage=completion_percentage,
        required_monthly_contribution=required_monthly_contrib,
        shortfall=remaining_amt,
        is_completed=is_completed,
        assumptions=assumptions,
    )
