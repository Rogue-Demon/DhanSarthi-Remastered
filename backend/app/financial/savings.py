"""
DhanSarthi Financial Engine — Savings Module.

Provides deterministic calculation of savings and savings rate percentage,
safely handling zero income conditions without division-by-zero errors.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import SavingsResult


def calculate_savings(
    total_income: Decimal,
    total_expenses: Decimal,
    reference_date: date | None = None,
) -> SavingsResult:
    """
    Calculate savings and savings rate percentage.

    Formulas:
        Savings = Total Income - Total Expenses
        Savings Rate (%) = (Savings / Total Income) * 100

    Args:
        total_income: Total monetary income (must be >= 0).
        total_expenses: Total monetary expenses (must be >= 0).
        reference_date: Optional calculation reference date.

    Returns:
        SavingsResult: Structured savings result.

    Raises:
        InvalidFinancialInput: If income or expenses are negative.
    """
    if total_income < Decimal("0"):
        raise InvalidFinancialInput(
            f"Total income cannot be negative: {total_income}",
            details={"total_income": str(total_income)},
        )
    if total_expenses < Decimal("0"):
        raise InvalidFinancialInput(
            f"Total expenses cannot be negative: {total_expenses}",
            details={"total_expenses": str(total_expenses)},
        )

    ref_date = reference_date or date.today()
    savings = total_income - total_expenses

    if total_income > Decimal("0"):
        raw_rate = (savings / total_income) * Decimal("100")
        savings_rate_percent = raw_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        is_income_zero = False
    else:
        savings_rate_percent = None
        is_income_zero = True

    return SavingsResult(
        total_income=total_income,
        total_expenses=total_expenses,
        savings=savings,
        savings_rate_percent=savings_rate_percent,
        is_income_zero=is_income_zero,
        reference_date=ref_date,
    )
