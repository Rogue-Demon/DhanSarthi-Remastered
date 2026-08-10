"""
DhanSarthi Financial Engine — Cash Flow Module.

Provides deterministic calculations for total income, total expenses, net cash
flow, category breakdowns, and top expense categories over a period.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import CashFlowInput, CashFlowResult


def calculate_cash_flow(input_data: CashFlowInput) -> CashFlowResult:
    """
    Calculate deterministic cash flow metrics from income and expense items.

    Args:
        input_data: CashFlowInput containing lists of income and expense items.

    Returns:
        CashFlowResult: Structured monetary cash flow breakdown.

    Raises:
        InvalidFinancialInput: If any income or expense item has a negative amount.
    """
    ref_date = input_data.reference_date or date.today()

    total_income = Decimal("0")
    income_by_cat: Dict[str, Decimal] = {}

    for item in input_data.incomes:
        if item.amount < Decimal("0"):
            raise InvalidFinancialInput(
                f"Income amount cannot be negative: {item.amount} in category '{item.category}'",
                details={"category": item.category, "amount": str(item.amount)},
            )
        total_income += item.amount
        cat = item.category or "OTHER"
        income_by_cat[cat] = income_by_cat.get(cat, Decimal("0")) + item.amount

    total_expenses = Decimal("0")
    expense_by_cat: Dict[str, Decimal] = {}

    for item in input_data.expenses:
        if item.amount < Decimal("0"):
            raise InvalidFinancialInput(
                f"Expense amount cannot be negative: {item.amount} in category '{item.category}'",
                details={"category": item.category, "amount": str(item.amount)},
            )
        total_expenses += item.amount
        cat = item.category or "OTHER"
        expense_by_cat[cat] = expense_by_cat.get(cat, Decimal("0")) + item.amount

    net_cash_flow = total_income - total_expenses

    # Top expense categories sorted descending by amount
    sorted_top_expenses: List[Tuple[str, Decimal]] = sorted(
        expense_by_cat.items(), key=lambda x: x[1], reverse=True
    )

    return CashFlowResult(
        total_income=total_income,
        total_expenses=total_expenses,
        net_cash_flow=net_cash_flow,
        income_by_category=income_by_cat,
        expense_by_category=expense_by_cat,
        top_expense_categories=sorted_top_expenses,
        period_days=input_data.period_days,
        reference_date=ref_date,
    )
