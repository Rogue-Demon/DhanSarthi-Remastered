"""Tests for Budget analysis module."""

from decimal import Decimal

import pytest

from app.financial import (
    BudgetAnalysisInput,
    BudgetCategoryInput,
    InvalidFinancialInput,
    analyze_budget,
)


def test_budget_analysis_normal():
    categories = [
        BudgetCategoryInput(category="Groceries", budget_amount=Decimal("10000"), actual_spending=Decimal("8000")),
        BudgetCategoryInput(category="Dining Out", budget_amount=Decimal("5000"), actual_spending=Decimal("7000")),
        BudgetCategoryInput(category="Utilities", budget_amount=Decimal("3000"), actual_spending=Decimal("3000")),
    ]
    res = analyze_budget(BudgetAnalysisInput(category_budgets=categories))

    assert res.total_budget == Decimal("18000")
    assert res.total_spending == Decimal("18000")
    assert res.total_remaining == Decimal("0")
    assert res.overall_utilization_percentage == Decimal("100.00")
    assert res.over_budget_categories == ["Dining Out"]

    # Category specific check
    dining = next(c for c in res.category_results if c.category == "Dining Out")
    assert dining.is_over_budget is True
    assert dining.over_budget_amount == Decimal("2000")
    assert dining.utilization_percentage == Decimal("140.00")

    groceries = next(c for c in res.category_results if c.category == "Groceries")
    assert groceries.is_over_budget is False
    assert groceries.remaining_budget == Decimal("2000")
    assert groceries.utilization_percentage == Decimal("80.00")


def test_budget_zero_budget():
    categories = [
        BudgetCategoryInput(category="Shopping", budget_amount=Decimal("0"), actual_spending=Decimal("500")),
    ]
    res = analyze_budget(BudgetAnalysisInput(category_budgets=categories))

    assert res.category_results[0].is_over_budget is True
    assert res.category_results[0].over_budget_amount == Decimal("500")


def test_budget_negative_input_raises_error():
    with pytest.raises(InvalidFinancialInput):
        analyze_budget(
            BudgetAnalysisInput(
                category_budgets=[
                    BudgetCategoryInput(category="Bad", budget_amount=Decimal("-100"), actual_spending=Decimal("50"))
                ]
            )
        )
