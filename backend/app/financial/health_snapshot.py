"""
Financial Health Snapshot & Deterministic Health Model for DhanSarthi — Phase K.

Provides presentation-independent, deterministic financial health evaluation
across 7 core dimensions without relying on non-authoritative LLM inference:
  1. Savings Health
  2. Expense Health
  3. Debt Health
  4. Liquidity / Emergency Fund Health
  5. Investment Health
  6. Goal Health
  7. Net Worth Health

Includes a transparent, documented, formula-based FinancialHealthScore (0-100 bounded).
If required data is missing, dimensions return status "INSUFFICIENT_DATA" rather than guessing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.financial.types import FinancialMetricsResult


_CONFIG = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)


class SavingsHealth(BaseModel):
    """Deterministic evaluation of user savings rate and monthly surplus."""

    model_config = _CONFIG

    status: str = Field(..., description="GOOD, ADEQUATE, POOR, NEGATIVE, or INSUFFICIENT_DATA")
    savings_amount: Optional[Decimal] = None
    savings_rate_percent: Optional[Decimal] = None
    net_cash_flow: Optional[Decimal] = None
    explanation: str = Field(..., description="Deterministic mathematical summary")


class ExpenseHealth(BaseModel):
    """Deterministic evaluation of spending efficiency and budget utilization."""

    model_config = _CONFIG

    status: str = Field(..., description="GOOD, MODERATE, HIGH_SPENDING, OVER_BUDGET, or INSUFFICIENT_DATA")
    total_expenses: Optional[Decimal] = None
    expense_ratio_percent: Optional[Decimal] = None  # Expenses / Income * 100
    essential_expenses: Optional[Decimal] = None
    discretionary_expenses: Optional[Decimal] = None
    budget_utilization_percent: Optional[Decimal] = None
    top_categories: List[tuple[str, Decimal]] = Field(default_factory=list)
    explanation: str = Field(...)


class DebtHealth(BaseModel):
    """Deterministic evaluation of debt burden and leverage."""

    model_config = _CONFIG

    status: str = Field(..., description="DEBT_FREE, HEALTHY, ELEVATED, SEVERE, or INSUFFICIENT_DATA")
    total_outstanding_debt: Optional[Decimal] = None
    monthly_emi_obligations: Optional[Decimal] = None
    dti_percent: Optional[Decimal] = None
    explanation: str = Field(...)


class LiquidityHealth(BaseModel):
    """Deterministic evaluation of liquid reserves and emergency fund coverage."""

    model_config = _CONFIG

    status: str = Field(..., description="OPTIMAL, SUFFICIENT, INADEQUATE, CRITICAL, or INSUFFICIENT_DATA")
    liquid_assets: Optional[Decimal] = None
    monthly_essential_expenses: Optional[Decimal] = None
    coverage_months: Optional[Decimal] = None
    explanation: str = Field(...)


class InvestmentHealth(BaseModel):
    """Deterministic evaluation of investment portfolio and asset allocation."""

    model_config = _CONFIG

    status: str = Field(..., description="DIVERSIFIED, GROWTH_ORIENTED, CONCENTRATED, UNINVESTED, or INSUFFICIENT_DATA")
    total_invested: Optional[Decimal] = None
    current_portfolio_value: Optional[Decimal] = None
    total_gain_loss: Optional[Decimal] = None
    return_percentage: Optional[Decimal] = None
    allocation_percentages: Dict[str, Decimal] = Field(default_factory=dict)
    explanation: str = Field(...)


class GoalHealth(BaseModel):
    """Deterministic evaluation of financial goal progress and feasibility."""

    model_config = _CONFIG

    status: str = Field(..., description="ON_TRACK, AT_RISK, BEHIND, NO_GOALS, or INSUFFICIENT_DATA")
    total_goals_count: int = 0
    completed_goals_count: int = 0
    average_completion_percent: Optional[Decimal] = None
    goals_requiring_higher_contribution: List[str] = Field(default_factory=list)
    explanation: str = Field(...)


class NetWorthHealth(BaseModel):
    """Deterministic evaluation of net worth balance sheet posture."""

    model_config = _CONFIG

    status: str = Field(..., description="STRONG, POSITIVE, NEUTRAL, NEGATIVE, or INSUFFICIENT_DATA")
    net_worth: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    asset_to_liability_ratio: Optional[Decimal] = None
    explanation: str = Field(...)


class DimensionScore(BaseModel):
    """Individual score breakdown for a health dimension."""

    model_config = _CONFIG

    dimension: str
    score: Optional[int] = Field(None, description="Score 0-100 or None if INSUFFICIENT_DATA")
    weight_percent: int
    formula: str
    status: str
    explanation: str


class FinancialHealthScore(BaseModel):
    """
    Transparent, documented Financial Health Score (0-100 bounded).

    Calculated deterministically using explicit weights across dimensions:
      - Savings Health (25%)
      - Liquidity Health (25%)
      - Debt Health (20%)
      - Investment Health (15%)
      - Goal Progress (15%)

    If total weight of available data is < 40%, overall_score is None and status is INSUFFICIENT_DATA.
    """

    model_config = _CONFIG

    overall_score: Optional[int] = Field(None, description="0-100 bounded score or None if INSUFFICIENT_DATA")
    status: str = Field(..., description="EXCELLENT, GOOD, FAIR, NEEDS_ATTENTION, or INSUFFICIENT_DATA")
    breakdown: List[DimensionScore] = Field(default_factory=list)
    data_completeness: str = Field(..., description="COMPLETE, GOOD, PARTIAL, LIMITED")
    formula_documentation: str = Field(
        default="Overall Score = Sum(Dimension Score * Dimension Weight) / Sum(Available Weights). Bounded to [0, 100]."
    )


class FinancialHealthSnapshot(BaseModel):
    """Complete consolidated financial health snapshot model for a user."""

    model_config = _CONFIG

    user_id: int
    reference_date: date
    savings: SavingsHealth
    expenses: ExpenseHealth
    debt: DebtHealth
    liquidity: LiquidityHealth
    investments: InvestmentHealth
    goals: GoalHealth
    net_worth: NetWorthHealth
    health_score: FinancialHealthScore


def _quantize_pct(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def build_financial_health_snapshot(
    user_id: int,
    metrics: FinancialMetricsResult,
    reference_date: Optional[date] = None,
) -> FinancialHealthSnapshot:
    """
    Build a deterministic, presentation-independent FinancialHealthSnapshot.

    Args:
        user_id: Authenticated user ID.
        metrics: Upstream FinancialMetricsResult computed by Financial Engine.
        reference_date: Optional reference date.

    Returns:
        FinancialHealthSnapshot: Fully populated deterministic snapshot.
    """
    ref_date = reference_date or metrics.reference_date or date.today()

    # 1. Savings Health
    if metrics.savings and metrics.savings.total_income > Decimal("0"):
        inc = metrics.savings.total_income
        exp = metrics.savings.total_expenses
        sav = metrics.savings.savings
        sav_pct = metrics.savings.savings_rate_percent or Decimal("0")

        if sav < Decimal("0"):
            s_status = "NEGATIVE"
            s_expl = f"Monthly expenses (₹{exp:,.2f}) exceed income (₹{inc:,.2f}), creating a net deficit of ₹{abs(sav):,.2f}."
        elif sav_pct >= Decimal("30.0"):
            s_status = "GOOD"
            s_expl = f"Excellent savings rate of {sav_pct:.1f}% (₹{sav:,.2f} saved from ₹{inc:,.2f} income)."
        elif sav_pct >= Decimal("15.0"):
            s_status = "ADEQUATE"
            s_expl = f"Moderate savings rate of {sav_pct:.1f}% (₹{sav:,.2f} saved from ₹{inc:,.2f} income)."
        else:
            s_status = "POOR"
            s_expl = f"Low savings rate of {sav_pct:.1f}% (only ₹{sav:,.2f} saved from ₹{inc:,.2f} income)."

        savings_health = SavingsHealth(
            status=s_status,
            savings_amount=sav,
            savings_rate_percent=_quantize_pct(sav_pct),
            net_cash_flow=metrics.cash_flow.net_cash_flow if metrics.cash_flow else sav,
            explanation=s_expl,
        )
    else:
        savings_health = SavingsHealth(
            status="INSUFFICIENT_DATA",
            explanation="Income data is not available to evaluate savings health.",
        )

    # 2. Expense Health
    if metrics.cash_flow and metrics.cash_flow.total_income > Decimal("0"):
        inc = metrics.cash_flow.total_income
        exp = metrics.cash_flow.total_expenses
        exp_ratio = (exp / inc * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        b_util = metrics.budget_summary.overall_utilization_percentage if metrics.budget_summary else None

        top_cats = metrics.cash_flow.top_expense_categories[:3] if metrics.cash_flow.top_expense_categories else []

        if exp_ratio > Decimal("100.0"):
            e_status = "OVER_BUDGET"
            e_expl = f"Total expenses consume {exp_ratio:.1f}% of income."
        elif exp_ratio > Decimal("80.0"):
            e_status = "HIGH_SPENDING"
            e_expl = f"Expenses consume {exp_ratio:.1f}% of income, leaving minimal buffer."
        elif exp_ratio > Decimal("50.0"):
            e_status = "MODERATE"
            e_expl = f"Expenses consume {exp_ratio:.1f}% of monthly income."
        else:
            e_status = "GOOD"
            e_expl = f"Healthy expense ratio of {exp_ratio:.1f}% of income."

        expense_health = ExpenseHealth(
            status=e_status,
            total_expenses=exp,
            expense_ratio_percent=exp_ratio,
            budget_utilization_percent=_quantize_pct(b_util) if b_util is not None else None,
            top_categories=top_cats,
            explanation=e_expl,
        )
    else:
        expense_health = ExpenseHealth(
            status="INSUFFICIENT_DATA",
            explanation="Expense records are insufficient to analyze spending health.",
        )

    # 3. Debt Health
    if metrics.debt:
        tot_debt = metrics.debt.total_liabilities_balance
        monthly_emi = metrics.debt.total_monthly_emi
        dti = metrics.debt.dti_percent

        if tot_debt == Decimal("0") and monthly_emi == Decimal("0"):
            d_status = "DEBT_FREE"
            d_expl = "You are currently debt-free with zero outstanding liabilities."
        elif dti is not None and dti > Decimal("45.0"):
            d_status = "SEVERE"
            d_expl = f"Debt-to-Income ratio is high at {dti:.1f}%, exceeding the safe 40% benchmark."
        elif dti is not None and dti > Decimal("30.0"):
            d_status = "ELEVATED"
            d_expl = f"Debt-to-Income ratio is elevated at {dti:.1f}%."
        else:
            d_status = "HEALTHY"
            d_expl = f"Debt burden is healthy (DTI: {dti:.1f}% if available, total EMI: ₹{monthly_emi:,.2f})."

        debt_health = DebtHealth(
            status=d_status,
            total_outstanding_debt=tot_debt,
            monthly_emi_obligations=monthly_emi,
            dti_percent=_quantize_pct(dti) if dti is not None else None,
            explanation=d_expl,
        )
    else:
        debt_health = DebtHealth(
            status="INSUFFICIENT_DATA",
            explanation="No liability or loan records found.",
        )

    # 4. Liquidity Health
    if metrics.net_worth:
        liq = metrics.net_worth.liquid_assets
        cov = metrics.emergency_fund_coverage_months
        essential = metrics.cash_flow.total_expenses if metrics.cash_flow else None

        if cov is not None:
            if cov >= Decimal("6.0"):
                l_status = "OPTIMAL"
                l_expl = f"Emergency reserves cover {cov:.1f} months of essential expenses (₹{liq:,.2f} liquid)."
            elif cov >= Decimal("3.0"):
                l_status = "SUFFICIENT"
                l_expl = f"Emergency reserves cover {cov:.1f} months of essential expenses."
            elif cov > Decimal("0"):
                l_status = "INADEQUATE"
                l_expl = f"Emergency reserves cover only {cov:.1f} months of essential expenses (minimum 3-6 months recommended)."
            else:
                l_status = "CRITICAL"
                l_expl = "Zero liquid emergency reserves found."
        elif liq > Decimal("0"):
            l_status = "SUFFICIENT"
            l_expl = f"Liquid assets of ₹{liq:,.2f} available (essential monthly expenses not explicitly set)."
        else:
            l_status = "CRITICAL"
            l_expl = "No liquid cash or bank balances recorded."

        liquidity_health = LiquidityHealth(
            status=l_status,
            liquid_assets=liq,
            monthly_essential_expenses=essential,
            coverage_months=_quantize_pct(cov) if cov is not None else None,
            explanation=l_expl,
        )
    else:
        liquidity_health = LiquidityHealth(
            status="INSUFFICIENT_DATA",
            explanation="Asset balance sheet records are not available to assess liquidity.",
        )

    # 5. Investment Health
    if metrics.portfolio_summary and metrics.portfolio_summary.total_invested > Decimal("0"):
        p = metrics.portfolio_summary
        tot_inv = p.total_invested
        cur_val = p.current_value
        gain = p.total_gain_loss
        ret_pct = p.total_return_percentage
        alloc = p.allocation_percentages

        conc_max = max(alloc.values()) if alloc else Decimal("0")

        if conc_max >= Decimal("80.0"):
            i_status = "CONCENTRATED"
            i_expl = f"Portfolio has high concentration ({conc_max:.1f}% in a single asset type)."
        else:
            i_status = "DIVERSIFIED"
            i_expl = f"Total portfolio value of ₹{cur_val:,.2f} with return of {ret_pct:.1f}%."

        investment_health = InvestmentHealth(
            status=i_status,
            total_invested=tot_inv,
            current_portfolio_value=cur_val,
            total_gain_loss=gain,
            return_percentage=_quantize_pct(ret_pct),
            allocation_percentages={k: _quantize_pct(v) for k, v in alloc.items()},
            explanation=i_expl,
        )
    else:
        investment_health = InvestmentHealth(
            status="UNINVESTED",
            total_invested=Decimal("0"),
            current_portfolio_value=Decimal("0"),
            explanation="No active investments recorded.",
        )

    # 6. Goal Health
    goal_health = GoalHealth(
        status="NO_GOALS",
        explanation="No active financial goals configured.",
    )

    # 7. Net Worth Health
    if metrics.net_worth:
        nw = metrics.net_worth.net_worth
        assets = metrics.net_worth.total_assets
        liab = metrics.net_worth.total_liabilities

        ratio = (assets / liab).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP) if liab > Decimal("0") else None

        if nw > Decimal("0"):
            nw_status = "POSITIVE" if liab > Decimal("0") else "STRONG"
            nw_expl = f"Positive net worth of ₹{nw:,.2f} (Assets: ₹{assets:,.2f}, Debt: ₹{liab:,.2f})."
        elif nw == Decimal("0"):
            nw_status = "NEUTRAL"
            nw_expl = "Net worth is currently ₹0."
        else:
            nw_status = "NEGATIVE"
            nw_expl = f"Negative net worth of ₹{nw:,.2f} as liabilities exceed assets."

        net_worth_health = NetWorthHealth(
            status=nw_status,
            net_worth=nw,
            total_assets=assets,
            total_liabilities=liab,
            asset_to_liability_ratio=ratio,
            explanation=nw_expl,
        )
    else:
        net_worth_health = NetWorthHealth(
            status="INSUFFICIENT_DATA",
            explanation="Net worth balance sheet is not available.",
        )

    # Compute Transparent Financial Health Score
    scores: List[DimensionScore] = []

    # Savings Score (25%)
    if savings_health.status != "INSUFFICIENT_DATA":
        sr = savings_health.savings_rate_percent or Decimal("0")
        s_score = min(100, max(0, int(sr * Decimal("2.5")))) if sr > Decimal("0") else 0
        scores.append(
            DimensionScore(
                dimension="Savings Rate",
                score=s_score,
                weight_percent=25,
                formula="Savings Rate % * 2.5 (capped at 100)",
                status=savings_health.status,
                explanation=savings_health.explanation,
            )
        )

    # Liquidity Score (25%)
    if liquidity_health.status != "INSUFFICIENT_DATA":
        cov = liquidity_health.coverage_months
        if cov is not None:
            l_score = min(100, max(0, int(cov * Decimal("16.66"))))  # 6 months = 100
        elif liquidity_health.liquid_assets and liquidity_health.liquid_assets > Decimal("0"):
            l_score = 50
        else:
            l_score = 0
        scores.append(
            DimensionScore(
                dimension="Emergency Reserve",
                score=l_score,
                weight_percent=25,
                formula="Coverage Months * 16.66 (6 months = 100)",
                status=liquidity_health.status,
                explanation=liquidity_health.explanation,
            )
        )

    # Debt Score (20%)
    if debt_health.status != "INSUFFICIENT_DATA":
        if debt_health.status == "DEBT_FREE":
            d_score = 100
        elif debt_health.dti_percent is not None:
            dti = debt_health.dti_percent
            d_score = min(100, max(0, int(Decimal("100") - dti * Decimal("2.0"))))
        else:
            d_score = 70
        scores.append(
            DimensionScore(
                dimension="Debt Burden",
                score=d_score,
                weight_percent=20,
                formula="100 - (DTI % * 2.0) (Debt Free = 100)",
                status=debt_health.status,
                explanation=debt_health.explanation,
            )
        )

    # Investment Score (15%)
    if investment_health.status != "INSUFFICIENT_DATA":
        if investment_health.status == "DIVERSIFIED":
            i_score = 85
        elif investment_health.status == "CONCENTRATED":
            i_score = 50
        elif investment_health.status == "UNINVESTED":
            i_score = 30
        else:
            i_score = 60
        scores.append(
            DimensionScore(
                dimension="Investment Diversification",
                score=i_score,
                weight_percent=15,
                formula="Asset Allocation Quality (Diversified=85, Concentrated=50, Uninvested=30)",
                status=investment_health.status,
                explanation=investment_health.explanation,
            )
        )

    # Calculate overall weighted score
    total_avail_weight = sum(s.weight_percent for s in scores)
    if total_avail_weight >= 40:
        weighted_sum = sum((s.score or 0) * s.weight_percent for s in scores)
        final_score = int(weighted_sum / total_avail_weight)
        final_score = max(0, min(100, final_score))

        if final_score >= 80:
            h_status = "EXCELLENT"
        elif final_score >= 60:
            h_status = "GOOD"
        elif final_score >= 40:
            h_status = "FAIR"
        else:
            h_status = "NEEDS_ATTENTION"

        completeness = "COMPLETE" if total_avail_weight == 85 else ("GOOD" if total_avail_weight >= 65 else "PARTIAL")
    else:
        final_score = None
        h_status = "INSUFFICIENT_DATA"
        completeness = "LIMITED"

    health_score_model = FinancialHealthScore(
        overall_score=final_score,
        status=h_status,
        breakdown=scores,
        data_completeness=completeness,
    )

    return FinancialHealthSnapshot(
        user_id=user_id,
        reference_date=ref_date,
        savings=savings_health,
        expenses=expense_health,
        debt=debt_health,
        liquidity=liquidity_health,
        investments=investment_health,
        goals=goal_health,
        net_worth=net_worth_health,
        health_score=health_score_model,
    )
