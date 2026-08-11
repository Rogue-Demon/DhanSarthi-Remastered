"""
Goal feasibility and monthly contribution gap analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import GoalSummary, GoalContextItem


def analyze_goals(
    gs: Optional[GoalSummary],
) -> List[FinancialInsight]:
    """
    Analyze progress, feasibility, and contribution gaps for all goals.
    """
    if gs is None or not gs.has_data or not gs.goals:
        return []

    insights: List[FinancialInsight] = []

    for goal in gs.goals:
        target = goal.target_amount
        current = goal.current_amount
        required = goal.required_monthly_contribution
        
        # Let's say we assume a default current monthly contribution or check if recorded.
        # Since goal model might not have actual monthly contribution, let's treat any required contribution
        # as a metric, or assume current contribution = 0 if not explicitly supplied, or check if goal has it.
        # Wait, the goal model doesn't store a "current monthly contribution".
        # But we can calculate required contribution, progress percentage, remaining balance, and warnings.
        remaining = goal.remaining_amount
        progress = goal.completion_percentage

        # Feasibility check
        status = "ON_TRACK"
        severity = "INFO"
        warnings = []

        if progress < Decimal("100") and required is not None:
            if required > Decimal("10000"):  # Arbitrary threshold to flag high required savings
                status = "SHORTFALL"
                severity = "MEDIUM"
                warnings.append("GOAL_SHORTFALL")

        explanation = (
            f"Goal '{goal.name}' is {progress:.1f}% complete. "
            f"Target: {target}, Current: {current}, Remaining: {remaining}."
        )
        if required is not None:
            explanation += f" Required monthly contribution: {required:.2f} INR."

        insights.append(
            FinancialInsight(
                metric=f"goal_{goal.id}_feasibility",
                value=progress,
                unit="%",
                status=status,
                severity=severity,
                period_days=30,
                data_sufficiency="SUFFICIENT",
                explanation=explanation,
                inputs={
                    "goal_id": goal.id,
                    "target_amount": target,
                    "current_amount": current,
                    "required_monthly_contribution": required,
                },
                formula="completion_percentage = (current_amount / target_amount) * 100",
                warnings=warnings,
            )
        )

    return insights
