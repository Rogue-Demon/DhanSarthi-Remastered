"""
Investment portfolio allocation and concentration analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional
from app.core.config import settings
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import InvestmentSummary


def analyze_investments(
    is_summary: Optional[InvestmentSummary],
) -> FinancialInsight:
    """
    Analyze portfolio allocation, gain/loss performance, and asset class concentration.
    """
    if is_summary is None or not is_summary.has_data:
        return FinancialInsight(
            metric="portfolio_performance",
            value=Decimal("0"),
            unit="INR",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=30,
            data_sufficiency="INSUFFICIENT",
            explanation="No investment holdings found in the user's profile.",
            inputs={},
            formula="gain_loss = current_value - total_invested",
            warnings=["MISSING_INVESTMENT_DATA"],
        )

    total_invested = is_summary.total_invested
    current_value = is_summary.current_value
    total_gain_loss = is_summary.total_gain_loss
    total_return_pct = is_summary.total_return_percentage

    # Concentration check (> 50%)
    concentration_threshold = Decimal(str(settings.investment_concentration_threshold))
    concentrated_types: List[str] = []
    
    for asset_type, pct in is_summary.allocation_percentages.items():
        if pct > concentration_threshold:
            concentrated_types.append(asset_type)

    status = "CONCENTRATION_DETECTED" if concentrated_types else "NORMAL"
    severity = "MEDIUM" if concentrated_types else "INFO"

    explanation = (
        f"Total Invested: {total_invested}, Current Value: {current_value}. "
        f"Overall Return: {total_return_pct:+.2f}% ({total_gain_loss:+.2f} INR)."
    )
    
    warnings: List[str] = []
    if concentrated_types:
        warnings.append("HIGH_INVESTMENT_CONCENTRATION")
        explanation += f" High portfolio concentration detected in: {', '.join(concentrated_types)}."

    return FinancialInsight(
        metric="portfolio_performance",
        value=total_gain_loss,
        unit="INR",
        status=status,
        severity=severity,
        period_days=30,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={
            "total_invested": total_invested,
            "current_value": current_value,
            "allocation_percentages": {k: float(v) for k, v in is_summary.allocation_percentages.items()},
        },
        formula="gain_loss = current_value - total_invested",
        warnings=warnings,
    )
