"""
Budget utilization and adherence analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import BudgetSummary


def analyze_budget(
    bs: Optional[BudgetSummary],
    history_overspending: Optional[Dict[str, int]] = None,
) -> FinancialInsight:
    """
    Analyze budget utilization levels and detect repeated over-budget behavior.
    """
    if bs is None or not bs.has_data or bs.total_budget == Decimal("0"):
        return FinancialInsight(
            metric="budget_utilization",
            value=Decimal("0"),
            unit="%",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=30,
            data_sufficiency="INSUFFICIENT",
            explanation="No budget records configured for the user.",
            inputs={},
            formula="utilization = (actual_spending / total_budget) * 100",
            warnings=["MISSING_BUDGET_DATA"],
        )

    utilization = bs.overall_utilization_percent

    # Status classification
    if utilization > Decimal("100"):
        status = "OVER_BUDGET"
        severity = "HIGH"
    elif utilization > Decimal("85"):
        status = "NEAR_LIMIT"
        severity = "MEDIUM"
    else:
        status = "ON_TRACK"
        severity = "INFO"

    # Identify repeated over budget behavior (3+ consecutive months)
    warnings: List[str] = []
    repeated_cats: List[str] = []
    if history_overspending:
        for cat, consecutive_count in history_overspending.items():
            if consecutive_count >= 3:
                repeated_cats.append(cat)

    if repeated_cats:
        status = "REPEATED_OVER_BUDGET"
        severity = "HIGH"
        warnings.append("REPEATED_BUDGET_OVERSPEND")

    explanation = f"Overall budget utilization is {utilization:.1f}% ({status.lower()})."
    if bs.over_budget_categories:
        explanation += f" Over-budget categories: {', '.join(bs.over_budget_categories)}."
    if repeated_cats:
        explanation += f" Repeated overspending detected in: {', '.join(repeated_cats)}."

    if status == "OVER_BUDGET":
        warnings.append("OVER_BUDGET_ALERT")

    return FinancialInsight(
        metric="budget_utilization",
        value=utilization,
        unit="%",
        status=status,
        severity=severity,
        period_days=30,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={
            "total_budget": bs.total_budget,
            "total_spending": bs.total_spending,
            "over_budget_categories": bs.over_budget_categories,
        },
        formula="utilization = (actual_spending / total_budget) * 100",
        warnings=warnings,
    )
