"""Tests for Goal analysis module."""

from datetime import date
from decimal import Decimal

import pytest

from app.financial import GoalInput, InvalidFinancialInput, analyze_goal


def test_goal_in_progress():
    inp = GoalInput(
        title="Emergency Fund",
        target_amount=Decimal("100000.00"),
        current_amount=Decimal("40000.00"),
        target_date=date(2027, 8, 10),
        expected_annual_return_percent=Decimal("0.00"),
        reference_date=date(2026, 8, 10),
    )
    res = analyze_goal(inp)

    assert res.title == "Emergency Fund"
    assert res.remaining_amount == Decimal("60000.00")
    assert res.completion_percentage == Decimal("40.00")
    assert res.time_remaining_months == 12
    assert res.required_monthly_contribution == Decimal("5000.00")  # 60,000 / 12
    assert res.is_completed is False


def test_goal_completed():
    inp = GoalInput(
        title="Laptop",
        target_amount=Decimal("80000.00"),
        current_amount=Decimal("85000.00"),
        target_date=date(2027, 1, 1),
        reference_date=date(2026, 8, 10),
    )
    res = analyze_goal(inp)

    assert res.remaining_amount == Decimal("0.00")
    assert res.completion_percentage == Decimal("100.00")
    assert res.required_monthly_contribution == Decimal("0.00")
    assert res.is_completed is True


def test_goal_past_target_date():
    inp = GoalInput(
        title="Old Goal",
        target_amount=Decimal("50000.00"),
        current_amount=Decimal("20000.00"),
        target_date=date(2025, 1, 1),
        reference_date=date(2026, 8, 10),
    )
    res = analyze_goal(inp)

    assert res.time_remaining_months == 0
    assert res.required_monthly_contribution is None
    assert res.is_completed is False


def test_goal_invalid_target_raises_error():
    with pytest.raises(InvalidFinancialInput):
        analyze_goal(
            GoalInput(
                title="Bad Goal",
                target_amount=Decimal("0"),
                current_amount=Decimal("0"),
                target_date=date(2027, 1, 1),
            )
        )
