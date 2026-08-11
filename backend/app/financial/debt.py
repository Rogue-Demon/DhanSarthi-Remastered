"""
DhanSarthi Financial Engine — Debt Analysis Module.

Provides deterministic debt metrics including total liabilities balance, total
monthly EMI burden, and Debt-to-Income (DTI) ratio.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import DebtAnalysisResult, LiabilityItemInput, LoanInput


def analyze_debt(
    liabilities: List[LiabilityItemInput],
    loans: Optional[List[LoanInput]] = None,
    gross_monthly_income: Decimal = Decimal("0"),
    reference_date: date | None = None,
) -> DebtAnalysisResult:
    """
    Analyze debt obligations and compute Debt-to-Income (DTI) ratio.

    Formula:
        DTI (%) = (Total Monthly Debt Payments / Gross Monthly Income) * 100

    Args:
        liabilities: List of liability input items.
        loans: Optional list of loan inputs (if loan payments not already in liabilities).
        gross_monthly_income: Gross monthly income (default 0).
        reference_date: Optional calculation reference date.

    Returns:
        DebtAnalysisResult: Structured debt metrics.

    Raises:
        InvalidFinancialInput: If balances, EMI, or income are negative.
    """
    if gross_monthly_income < Decimal("0"):
        raise InvalidFinancialInput(
            f"Gross monthly income cannot be negative: {gross_monthly_income}",
            details={"gross_monthly_income": str(gross_monthly_income)},
        )

    ref_date = reference_date or date.today()
    total_liabilities_balance = Decimal("0")
    total_monthly_emi = Decimal("0")

    for l in liabilities:
        if l.outstanding_balance < Decimal("0"):
            raise InvalidFinancialInput(
                f"Liability balance cannot be negative: {l.outstanding_balance} for '{l.name}'",
                details={"name": l.name, "balance": str(l.outstanding_balance)},
            )
        if l.monthly_payment < Decimal("0"):
            raise InvalidFinancialInput(
                f"Monthly payment cannot be negative: {l.monthly_payment} for '{l.name}'",
                details={"name": l.name, "payment": str(l.monthly_payment)},
            )
        total_liabilities_balance += l.outstanding_balance
        total_monthly_emi += l.monthly_payment

    if loans:
        for loan in loans:
            if loan.principal < Decimal("0"):
                raise InvalidFinancialInput(
                    f"Loan principal cannot be negative: {loan.principal}",
                    details={"principal": str(loan.principal)},
                )
            p = loan.principal
            rate = loan.annual_interest_rate_percent
            months = loan.tenure_months

            if p > Decimal("0") and months > 0:
                if rate > Decimal("0"):
                    r = rate / Decimal("12") / Decimal("100")
                    try:
                        import math
                        power = Decimal(str(math.pow(1 + float(r), months)))
                        emi = p * r * power / (power - 1)
                        emi = emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    except Exception:
                        emi = p / Decimal(months)
                else:
                    emi = p / Decimal(months)
                total_monthly_emi += emi
                total_liabilities_balance += p

    if gross_monthly_income > Decimal("0"):
        raw_dti = (total_monthly_emi / gross_monthly_income) * Decimal("100")
        dti_percent = raw_dti.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        dti_percent = None

    return DebtAnalysisResult(
        total_liabilities_balance=total_liabilities_balance,
        total_monthly_emi=total_monthly_emi,
        dti_percent=dti_percent,
        reference_date=ref_date,
    )
