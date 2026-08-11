"""
Expense and category concentration analyzer with statistical anomaly detection.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import CashFlowSummary

# Core essential categories pattern matching
ESSENTIAL_CATEGORIES = {
    "housing",
    "rent",
    "food",
    "groceries",
    "utilities",
    "healthcare",
    "medical",
    "transport",
    "transportation",
    "education",
    "debt payments",
    "emi",
    "insurance",
}


def analyze_expenses(
    cf: Optional[CashFlowSummary],
    period_days: Optional[int],
    transactions: Optional[List[Any]] = None,
) -> FinancialInsight:
    """
    Analyze total spending, fixed/variable split, and category concentrations.
    """
    if cf is None or not cf.has_data or cf.total_expenses == Decimal("0"):
        return FinancialInsight(
            metric="expense_concentration",
            value={},
            unit="%",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=period_days,
            data_sufficiency="INSUFFICIENT",
            explanation="No expense information available to analyze concentration.",
            inputs={},
            formula="category_percentage = (category_spending / total_expenses) * 100",
            warnings=["MISSING_EXPENSE_DATA"],
        )

    total_expenses = cf.total_expenses
    category_percentages: Dict[str, Decimal] = {}
    high_concentration_categories: List[str] = []
    warnings: List[str] = []

    # 1. Identify category concentrations (>30%)
    for cat, amount in cf.expense_by_category.items():
        pct = (amount / total_expenses) * Decimal("100")
        category_percentages[cat] = pct
        if pct > Decimal("30"):
            high_concentration_categories.append(cat)

    # 2. Variable vs Essential split
    essential_spending = Decimal("0")
    for cat, amount in cf.expense_by_category.items():
        if cat.lower() in ESSENTIAL_CATEGORIES or any(esc in cat.lower() for esc in ESSENTIAL_CATEGORIES):
            essential_spending += amount

    essential_pct = (essential_spending / total_expenses) * Decimal("100")
    variable_pct = Decimal("100") - essential_pct

    # 3. Detect anomalies in transactions if provided
    anomalies: List[Dict[str, Any]] = []
    if transactions:
        # Group transaction amounts by category
        cat_amounts: Dict[str, List[Decimal]] = {}
        for tx in transactions:
            cat = getattr(tx, "category", "Other")
            amount = abs(Decimal(str(getattr(tx, "amount", 0))))
            cat_amounts.setdefault(cat, []).append(amount)

        for cat, amounts in cat_amounts.items():
            if len(amounts) >= 3:
                # Compute statistical mean and standard deviation
                n = len(amounts)
                mean = sum(amounts) / n
                
                # Standard deviation
                if n >= 2:
                    variance = sum((x - mean) ** 2 for x in amounts) / (n - 1)
                    std_dev = Decimal(str(math.sqrt(float(variance))))
                else:
                    std_dev = Decimal("0")

                threshold = mean + Decimal("2") * std_dev
                
                # Check for anomalies
                for tx in transactions:
                    if getattr(tx, "category", "Other") == cat:
                        val = abs(Decimal(str(getattr(tx, "amount", 0))))
                        if val > threshold and val > Decimal("1000"):  # only flag significant anomalies
                            anomalies.append({
                                "id": getattr(tx, "id", None),
                                "description": getattr(tx, "description", ""),
                                "amount": val,
                                "category": cat,
                                "threshold": threshold,
                            })

    status = "CONCENTRATION_DETECTED" if high_concentration_categories else "NORMAL"
    severity = "MEDIUM" if high_concentration_categories else "INFO"

    explanation = (
        f"Essential spending accounts for {essential_pct:.1f}% of expenses. "
        f"Variable spending accounts for {variable_pct:.1f}%."
    )
    if high_concentration_categories:
        explanation += f" High spending concentration detected in: {', '.join(high_concentration_categories)}."

    if anomalies:
        warnings.append("UNUSUAL_TRANSACTIONS_DETECTED")
        explanation += f" Found {len(anomalies)} unusual transactions exceeding category averages."

    return FinancialInsight(
        metric="expense_concentration",
        value={
            "category_percentages": {k: float(v) for k, v in category_percentages.items()},
            "essential_percentage": float(essential_pct),
            "variable_percentage": float(variable_pct),
            "anomalies_count": len(anomalies),
        },
        unit="%",
        status=status,
        severity=severity,
        period_days=period_days,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={
            "expense_by_category": {k: float(v) for k, v in cf.expense_by_category.items()},
            "total_expenses": float(total_expenses),
        },
        formula="essential_percentage = (essential_expenses / total_expenses) * 100",
        warnings=warnings,
    )
