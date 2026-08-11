"""
Emergency fund and liquidity analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from app.core.config import settings
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import FinancialHealthSummary, NetWorthSummary


def analyze_emergency_fund(
    fhs: Optional[FinancialHealthSummary],
    nw: Optional[NetWorthSummary],
    essential_monthly_expenses: Optional[Decimal],
) -> FinancialInsight:
    """
    Analyze emergency fund coverage in months relative to essential expenses.
    """
    liquid_savings = nw.liquid_assets if nw else Decimal("0")
    coverage = fhs.emergency_fund_months if fhs else None
    
    if (coverage is None or coverage == Decimal("0")) and essential_monthly_expenses and essential_monthly_expenses > Decimal("0"):
        from decimal import ROUND_HALF_UP
        coverage = (liquid_savings / essential_monthly_expenses).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if coverage is None:
        return FinancialInsight(
            metric="emergency_fund_months",
            value=Decimal("0"),
            unit="months",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=30,
            data_sufficiency="INSUFFICIENT",
            explanation="Emergency fund coverage cannot be calculated without essential expenses or liquid asset information.",
            inputs={},
            formula="emergency_fund_months = liquid_savings / essential_monthly_expenses",
            warnings=["MISSING_EMERGENCY_FUND_DATA"],
        )
    
    warning_threshold = Decimal(str(settings.emergency_fund_warning_months))
    target_threshold = Decimal(str(settings.emergency_fund_target_months))

    if coverage < warning_threshold:
        status = "LOW"
        severity = "HIGH"
    elif coverage < target_threshold:
        status = "MODERATE"
        severity = "LOW"
    else:
        status = "HIGH"
        severity = "INFO"

    explanation = f"Emergency fund covers {coverage:.1f} months of essential expenses, which is {status.lower()}."
    warnings: List[str] = []
    if coverage < warning_threshold:
        warnings.append("LOW_EMERGENCY_COVERAGE")

    return FinancialInsight(
        metric="emergency_fund_months",
        value=coverage,
        unit="months",
        status=status,
        severity=severity,
        period_days=30,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={
            "liquid_savings": liquid_savings,
            "essential_monthly_expenses": essential_monthly_expenses,
        },
        formula="emergency_fund_months = liquid_savings / essential_monthly_expenses",
        warnings=warnings,
    )
