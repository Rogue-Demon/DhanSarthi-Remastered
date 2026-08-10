"""
DhanSarthi Financial Engine — Budget Analysis Module.

Provides deterministic calculations for category budget utilization, remaining
budgets, and over-budget category identification.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import (
    BudgetAnalysisInput,
    BudgetAnalysisResult,
    BudgetCategoryResult,
)


def analyze_budget(input_data: BudgetAnalysisInput) -> BudgetAnalysisResult:
    """
    Analyze budget allocations against actual spending.

    Args:
        input_data: BudgetAnalysisInput containing category budgets.

    Returns:
        BudgetAnalysisResult: Aggregated and per-category budget analysis.

    Raises:
        InvalidFinancialInput: If budget amounts or actual spending are negative.
    """
    total_budget = Decimal("0")
    total_spending = Decimal("0")
    category_results: List[BudgetCategoryResult] = []
    over_budget_categories: List[str] = []

    for cat in input_data.category_budgets:
        if cat.budget_amount < Decimal("0"):
            raise InvalidFinancialInput(
                f"Budget amount cannot be negative: {cat.budget_amount} for '{cat.category}'",
                details={"category": cat.category, "budget_amount": str(cat.budget_amount)},
            )
        if cat.actual_spending < Decimal("0"):
            raise InvalidFinancialInput(
                f"Actual spending cannot be negative: {cat.actual_spending} for '{cat.category}'",
                details={"category": cat.category, "actual_spending": str(cat.actual_spending)},
            )

        b_amt = cat.budget_amount
        s_amt = cat.actual_spending
        remaining = b_amt - s_amt
        is_over = s_amt > b_amt
        over_amt = max(Decimal("0"), s_amt - b_amt)

        if b_amt > Decimal("0"):
            raw_util = (s_amt / b_amt) * Decimal("100")
            utilization_pct = raw_util.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            utilization_pct = Decimal("0") if s_amt == Decimal("0") else Decimal("100.00")

        if is_over:
            over_budget_categories.append(cat.category)

        total_budget += b_amt
        total_spending += s_amt

        category_results.append(
            BudgetCategoryResult(
                category=cat.category,
                budget_amount=b_amt,
                actual_spending=s_amt,
                remaining_budget=remaining,
                utilization_percentage=utilization_pct,
                is_over_budget=is_over,
                over_budget_amount=over_amt,
            )
        )

    total_remaining = total_budget - total_spending

    if total_budget > Decimal("0"):
        raw_overall_util = (total_spending / total_budget) * Decimal("100")
        overall_utilization_pct = raw_overall_util.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        overall_utilization_pct = Decimal("0")

    return BudgetAnalysisResult(
        total_budget=total_budget,
        total_spending=total_spending,
        total_remaining=total_remaining,
        overall_utilization_percentage=overall_utilization_pct,
        category_results=category_results,
        over_budget_categories=over_budget_categories,
    )
