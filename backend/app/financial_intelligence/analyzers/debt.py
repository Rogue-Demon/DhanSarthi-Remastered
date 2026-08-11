"""
Debt burden and Debt-to-Income (DTI) analyzer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from app.core.config import settings
from app.financial_intelligence.schemas import FinancialInsight
from app.schemas.dashboard import DebtSummary


def analyze_debt_burden(
    ds: Optional[DebtSummary],
) -> FinancialInsight:
    """
    Analyze Debt-to-Income (DTI) and monthly debt obligations.
    """
    if ds is None or not ds.has_data or ds.dti_percent is None:
        return FinancialInsight(
            metric="debt_to_income",
            value=Decimal("0"),
            unit="%",
            status="INSUFFICIENT_DATA",
            severity="LOW",
            period_days=30,
            data_sufficiency="INSUFFICIENT",
            explanation="Debt-to-Income ratio cannot be computed due to missing income or debt data.",
            inputs={},
            formula="DTI = (monthly_debt_obligations / gross_monthly_income) * 100",
            warnings=["MISSING_DEBT_OR_INCOME_DATA"],
        )

    dti = ds.dti_percent
    high_threshold = Decimal(str(settings.dti_threshold_high))
    very_high_threshold = Decimal(str(settings.dti_threshold_very_high))

    if dti > very_high_threshold:
        status = "VERY_HIGH"
        severity = "CRITICAL"
    elif dti > high_threshold:
        status = "HIGH"
        severity = "HIGH"
    elif dti > Decimal("20"):
        status = "MODERATE"
        severity = "MEDIUM"
    else:
        status = "LOW"
        severity = "INFO"

    explanation = f"Debt-to-Income ratio of {dti:.1f}% is considered {status.lower()}."
    warnings: List[str] = []
    if dti > high_threshold:
        warnings.append("HIGH_DEBT_BURDEN")

    return FinancialInsight(
        metric="debt_to_income",
        value=dti,
        unit="%",
        status=status,
        severity=severity,
        period_days=30,
        data_sufficiency="SUFFICIENT",
        explanation=explanation,
        inputs={
            "total_debt": ds.total_debt,
            "monthly_obligations": ds.monthly_obligations,
            "dti_percent": dti,
        },
        formula="DTI = (monthly_debt_obligations / gross_monthly_income) * 100",
        warnings=warnings,
    )
