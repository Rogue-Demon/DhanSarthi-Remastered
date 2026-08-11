"""
Cash flow and savings rate analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import CashFlowSummary


def analyze_cash_flow(
    cf: Optional[CashFlowSummary],
    period_days: Optional[int],
    history_flows: Optional[List[Decimal]] = None,
) -> FinancialInsight:
    """
    Analyze net cash flow status and monthly savings rate.
    """
    if cf is None or not cf.has_data:
        return FinancialInsight(
            metric="net_cash_flow",
            value=Decimal("0"),
            unit="INR",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=period_days,
            data_sufficiency="INSUFFICIENT",
            explanation="No cash flow information available in the system.",
            inputs={},
            formula="net_cash_flow = total_income - total_expenses",
            warnings=["MISSING_CASH_FLOW_DATA"],
        )

    # Net Cash Flow Status
    status = "POSITIVE" if cf.net_cash_flow > 0 else ("BREAK_EVEN" if cf.net_cash_flow == Decimal("0") else "NEGATIVE")
    severity = "INFO" if status == "POSITIVE" else ("LOW" if status == "BREAK_EVEN" else "HIGH")

    explanation = (
        f"Net Cash Flow is {status.lower()}. "
        f"Total Income: {cf.total_income}, Total Expenses: {cf.total_expenses}."
    )

    # Trend calculation
    warnings = []
    if status == "NEGATIVE":
        warnings.append("NEGATIVE_CASH_FLOW")

    if history_flows and len(history_flows) >= 2:
        # Simple MoM trend calculation
        # Let's say history_flows is in reverse chronological order: [current_month, last_month, month_before]
        current = history_flows[0]
        previous = history_flows[1]
        
        # Determine trend direction
        if previous != Decimal("0"):
            change_pct = ((current - previous) / abs(previous)) * Decimal("100")
        else:
            change_pct = Decimal("100") if current > 0 else (Decimal("-100") if current < 0 else Decimal("0"))
            
        if abs(change_pct) <= Decimal("5"):
            trend = "stable"
        elif change_pct > Decimal("5"):
            trend = "improving"
        else:
            trend = "declining"
            
        explanation += f" Cash flow trend is {trend} (MoM change: {change_pct:+.1f}%)."
    else:
        trend = "stable"

    return FinancialInsight(
        metric="net_cash_flow",
        value=cf.net_cash_flow,
        unit="INR",
        status=status,
        severity=severity,
        period_days=period_days,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={"total_income": cf.total_income, "total_expenses": cf.total_expenses},
        formula="net_cash_flow = total_income - total_expenses",
        warnings=warnings,
    )


def analyze_savings(
    cf: Optional[CashFlowSummary],
    period_days: Optional[int],
) -> FinancialInsight:
    """
    Analyze savings and savings rate health.
    """
    if cf is None or not cf.has_data or cf.total_income == Decimal("0"):
        return FinancialInsight(
            metric="savings_rate",
            value=Decimal("0"),
            unit="%",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=period_days,
            data_sufficiency="INSUFFICIENT",
            explanation="Savings rate cannot be computed because total income is missing or zero.",
            inputs={},
            formula="savings_rate = (savings / total_income) * 100",
            warnings=["INSUFFICIENT_INCOME_FOR_SAVINGS"],
        )

    savings = cf.savings
    savings_rate = cf.savings_rate_percent or Decimal("0")

    # Range check
    if savings_rate >= Decimal("20"):
        status = "HEALTHY"
        severity = "INFO"
    elif savings_rate > Decimal("0"):
        status = "MODERATE"
        severity = "LOW"
    else:
        status = "LOW"
        severity = "MEDIUM"

    explanation = f"Savings rate of {savings_rate:.1f}% is considered {status.lower()}."
    warnings = []
    if status == "LOW":
        warnings.append("LOW_SAVINGS_RATE")

    return FinancialInsight(
        metric="savings_rate",
        value=savings_rate,
        unit="%",
        status=status,
        severity=severity,
        period_days=period_days,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={"savings": savings, "total_income": cf.total_income},
        formula="savings_rate = (savings / total_income) * 100",
        warnings=warnings,
    )
