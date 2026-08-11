"""
Centralized business rules and thresholds for warnings and financial opportunities.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from app.core.config import settings
from app.schemas.dashboard import DashboardResponse


def evaluate_warnings(db_dash: DashboardResponse) -> List[str]:
    """
    Evaluate system-wide warnings based on dashboard aggregation metrics.
    """
    warnings: List[str] = []
    
    # 1. Cash flow warning
    if db_dash.cash_flow and db_dash.cash_flow.has_data:
        if db_dash.cash_flow.net_cash_flow < Decimal("0"):
            warnings.append("NEGATIVE_CASH_FLOW")

    # 2. DTI warning
    if db_dash.debt and db_dash.debt.has_data and db_dash.debt.dti_percent is not None:
        high_threshold = Decimal(str(settings.dti_threshold_high))
        if db_dash.debt.dti_percent > high_threshold:
            warnings.append("HIGH_DEBT_BURDEN")

    # 3. Emergency fund warning
    if db_dash.financial_health and db_dash.financial_health.emergency_fund_months is not None:
        warning_limit = Decimal(str(settings.emergency_fund_warning_months))
        if db_dash.financial_health.emergency_fund_months < warning_limit:
            warnings.append("LOW_EMERGENCY_COVERAGE")

    # 4. Budget overspend
    if db_dash.budgets and db_dash.budgets.has_data:
        if db_dash.budgets.overall_utilization_percent > Decimal("100"):
            warnings.append("BUDGET_OVERSPEND")

    # 5. Goal shortfall warning
    if db_dash.goals and db_dash.goals.has_data:
        for goal in db_dash.goals.goals:
            # If required monthly contribution exists and is high, flag it
            req = goal.required_monthly_contribution
            if req and req > Decimal("10000"):
                warnings.append("GOAL_SHORTFALL")
                break

    # 6. Investment concentration warning
    if db_dash.investments and db_dash.investments.has_data:
        conc_threshold = Decimal(str(settings.investment_concentration_threshold))
        for asset, pct in db_dash.investments.allocation_percentages.items():
            if pct > conc_threshold:
                warnings.append("HIGH_INVESTMENT_CONCENTRATION")
                break

    return warnings


def evaluate_opportunities(db_dash: DashboardResponse) -> List[str]:
    """
    Evaluate financial opportunities based on dashboard aggregation metrics.
    """
    opportunities: List[str] = []

    # 1. Cash flow surplus opportunity
    if db_dash.cash_flow and db_dash.cash_flow.has_data:
        if db_dash.cash_flow.net_cash_flow > Decimal("1000"):
            opportunities.append("POSITIVE_MONTHLY_SURPLUS")

    # 2. Low debt burden opportunity
    if db_dash.debt and db_dash.debt.has_data and db_dash.debt.dti_percent is not None:
        if db_dash.debt.dti_percent < Decimal("15"):
            opportunities.append("LOW_DEBT_BURDEN")

    # 3. Unused budget capacity
    if db_dash.budgets and db_dash.budgets.has_data:
        util = db_dash.budgets.overall_utilization_percent
        if util > Decimal("0") and util < Decimal("70"):
            opportunities.append("UNUSED_BUDGET_CAPACITY")

    # 4. Excess cash reserve (emergency fund covers >12 months)
    if db_dash.financial_health and db_dash.financial_health.emergency_fund_months is not None:
        if db_dash.financial_health.emergency_fund_months > Decimal("12"):
            opportunities.append("EXCESS_CASH_RESERVE")

    # 5. Goal contribution capacity (if positive cash flow and has shortfall goals)
    if "POSITIVE_MONTHLY_SURPLUS" in opportunities and db_dash.goals and db_dash.goals.has_data:
        has_shortfall = False
        for goal in db_dash.goals.goals:
            req = goal.required_monthly_contribution
            if req and req > Decimal("0") and goal.completion_percentage < Decimal("100"):
                has_shortfall = True
                break
        if has_shortfall:
            opportunities.append("GOAL_CONTRIBUTION_CAPACITY")

    return opportunities
