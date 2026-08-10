"""
DhanSarthi Financial Engine — Investments & Portfolio Module.

Provides deterministic SIP calculations, compound growth projections, individual
investment returns, portfolio summary, and asset allocation percentages.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict

from app.financial.exceptions import InvalidFinancialInput, InvalidInvestmentParameters
from app.financial.types import (
    CompoundingInput,
    CompoundingResult,
    InvestmentItemInput,
    InvestmentReturnResult,
    PortfolioInput,
    PortfolioSummaryResult,
    SIPCalculationResult,
    SIPInput,
)


def calculate_compounding(input_data: CompoundingInput) -> CompoundingResult:
    """
    Calculate generic compound growth for initial principal and optional periodic contributions.

    Args:
        input_data: CompoundingInput payload.

    Returns:
        CompoundingResult: Structured future value and interest earned.

    Raises:
        InvalidInvestmentParameters: If inputs violate numerical domain rules.
    """
    a0 = input_data.principal
    p = input_data.periodic_contribution
    rate_pct = input_data.annual_rate_percent
    m = input_data.compounding_frequency_per_year
    t = input_data.duration_years

    if a0 < Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Initial principal cannot be negative: {a0}",
            details={"principal": str(a0)},
        )
    if p < Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Periodic contribution cannot be negative: {p}",
            details={"periodic_contribution": str(p)},
        )
    if rate_pct < Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Annual rate cannot be negative: {rate_pct}",
            details={"annual_rate_percent": str(rate_pct)},
        )
    if m <= 0:
        raise InvalidInvestmentParameters(
            f"Compounding frequency per year must be positive: {m}",
            details={"compounding_frequency_per_year": m},
        )
    if t <= Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Duration in years must be positive: {t}",
            details={"duration_years": str(t)},
        )

    n_periods = int((Decimal(m) * t).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    if rate_pct == Decimal("0"):
        raw_fv = a0 + (p * Decimal(n_periods))
    else:
        r = (rate_pct / Decimal("100")) / Decimal(m)
        factor = (Decimal("1") + r) ** n_periods
        principal_growth = a0 * factor
        contribution_growth = p * ((factor - Decimal("1")) / r) * (Decimal("1") + r)
        raw_fv = principal_growth + contribution_growth

    total_invested = a0 + (p * Decimal(n_periods))
    future_value = raw_fv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    interest_earned = future_value - total_invested

    assumptions: Dict[str, Any] = {
        "principal": str(a0),
        "periodic_contribution": str(p),
        "annual_rate_percent": str(rate_pct),
        "compounding_frequency_per_year": m,
        "duration_years": str(t),
        "total_periods": n_periods,
    }

    return CompoundingResult(
        total_invested=total_invested,
        future_value=future_value,
        interest_earned=interest_earned,
        assumptions=assumptions,
    )


def calculate_sip(input_data: SIPInput) -> SIPCalculationResult:
    """
    Calculate Systematic Investment Plan (SIP) future value and gains.

    Formula:
        FV = P * [ (1 + r)^n - 1 ] / r * (1 + r)
        where:
            P = Monthly contribution
            r = Expected monthly return rate = (Annual Rate / 100) / 12
            n = Total months = Duration in years * 12

    Args:
        input_data: SIPInput payload.

    Returns:
        SIPCalculationResult: Structured projection result with explicit assumptions.

    Raises:
        InvalidInvestmentParameters: If contribution <= 0, rate < 0, or duration <= 0.
    """
    p = input_data.monthly_contribution
    rate_pct = input_data.expected_annual_return_percent
    duration_yrs = input_data.duration_years

    if p <= Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Monthly contribution must be strictly positive: {p}",
            details={"monthly_contribution": str(p)},
        )
    if rate_pct < Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Expected annual return rate cannot be negative: {rate_pct}",
            details={"expected_annual_return_percent": str(rate_pct)},
        )
    if duration_yrs <= Decimal("0"):
        raise InvalidInvestmentParameters(
            f"Investment duration in years must be strictly positive: {duration_yrs}",
            details={"duration_years": str(duration_yrs)},
        )

    n_months = int((duration_yrs * Decimal("12")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    total_invested = p * Decimal(n_months)

    if rate_pct == Decimal("0"):
        raw_fv = total_invested
    else:
        r = (rate_pct / Decimal("100")) / Decimal("12")
        factor = (Decimal("1") + r) ** n_months
        raw_fv = p * ((factor - Decimal("1")) / r) * (Decimal("1") + r)

    estimated_future_value = raw_fv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    estimated_gains = estimated_future_value - total_invested

    assumptions: Dict[str, Any] = {
        "monthly_contribution": str(p),
        "expected_annual_return_percent": str(rate_pct),
        "duration_years": str(duration_yrs),
        "total_months": n_months,
        "disclaimer": "Assumed return rate for projection purposes; returns are not guaranteed.",
    }

    return SIPCalculationResult(
        monthly_contribution=p,
        expected_annual_return_percent=rate_pct,
        duration_years=duration_yrs,
        total_invested=total_invested,
        estimated_future_value=estimated_future_value,
        estimated_gains=estimated_gains,
        assumptions=assumptions,
    )


def calculate_investment_return(
    item: InvestmentItemInput,
) -> InvestmentReturnResult:
    """
    Calculate performance metrics for a single investment holding.

    Args:
        item: InvestmentItemInput item.

    Returns:
        InvestmentReturnResult: Absolute gain/loss and return percentage.

    Raises:
        InvalidFinancialInput: If invested amount or current value are negative.
    """
    if item.invested_amount < Decimal("0"):
        raise InvalidFinancialInput(
            f"Invested amount cannot be negative: {item.invested_amount} for '{item.name}'",
            details={"name": item.name, "invested_amount": str(item.invested_amount)},
        )
    if item.current_value < Decimal("0"):
        raise InvalidFinancialInput(
            f"Current value cannot be negative: {item.current_value} for '{item.name}'",
            details={"name": item.name, "current_value": str(item.current_value)},
        )

    gain_loss = item.current_value - item.invested_amount

    if item.invested_amount > Decimal("0"):
        raw_return = (gain_loss / item.invested_amount) * Decimal("100")
        return_pct = raw_return.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        return_pct = Decimal("0")

    return InvestmentReturnResult(
        name=item.name,
        invested_amount=item.invested_amount,
        current_value=item.current_value,
        gain_loss=gain_loss,
        return_percentage=return_pct,
        absolute_return=gain_loss,
    )


def analyze_portfolio(input_data: PortfolioInput) -> PortfolioSummaryResult:
    """
    Analyze an overall investment portfolio, calculating total performance and allocation percentages.

    Args:
        input_data: PortfolioInput payload containing list of investment holdings.

    Returns:
        PortfolioSummaryResult: Aggregated portfolio metrics and type allocation breakdown.

    Raises:
        InvalidFinancialInput: If any investment has negative value/invested amounts.
    """
    total_invested = Decimal("0")
    total_current_value = Decimal("0")
    allocation_by_type: Dict[str, Decimal] = {}

    for inv in input_data.investments:
        if inv.invested_amount < Decimal("0") or inv.current_value < Decimal("0"):
            raise InvalidFinancialInput(
                f"Investment values cannot be negative for '{inv.name}'",
                details={
                    "name": inv.name,
                    "invested_amount": str(inv.invested_amount),
                    "current_value": str(inv.current_value),
                },
            )
        total_invested += inv.invested_amount
        total_current_value += inv.current_value

        inv_type = inv.investment_type.value if hasattr(inv.investment_type, "value") else str(inv.investment_type)
        allocation_by_type[inv_type] = (
            allocation_by_type.get(inv_type, Decimal("0")) + inv.current_value
        )

    total_gain_loss = total_current_value - total_invested

    if total_invested > Decimal("0"):
        raw_total_return = (total_gain_loss / total_invested) * Decimal("100")
        total_return_pct = raw_total_return.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        total_return_pct = Decimal("0")

    allocation_percentages: Dict[str, Decimal] = {}
    basis = total_current_value if total_current_value > Decimal("0") else total_invested

    if basis > Decimal("0"):
        for inv_type, type_val in allocation_by_type.items():
            raw_pct = (type_val / basis) * Decimal("100")
            allocation_percentages[inv_type] = raw_pct.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    return PortfolioSummaryResult(
        total_invested=total_invested,
        current_value=total_current_value,
        total_gain_loss=total_gain_loss,
        total_return_percentage=total_return_pct,
        allocation_by_type=allocation_by_type,
        allocation_percentages=allocation_percentages,
    )
