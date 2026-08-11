"""
Pydantic response schemas for the DhanSarthi Dashboard and Financial Context API.

These schemas define the data contract between the backend and:
  - The React frontend (via GET /api/v1/dashboard)
  - Future AI Advisor / RAG (via GET /api/v1/financial/context)

Design rules enforced here:
  - No password, password_hash, JWT, or auth data.
  - ``None`` means "no data / insufficient data" — not the same as zero.
  - All monetary amounts use ``Decimal`` for precision.
  - ``context_version`` allows future AI systems to handle schema evolution.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Period
# ---------------------------------------------------------------------------


class PeriodInfo(BaseModel):
    """Defines the time window used for all flow-based calculations."""

    start_date: date
    end_date: date
    period_days: int


# ---------------------------------------------------------------------------
# User / Profile context
# ---------------------------------------------------------------------------


class UserContextInfo(BaseModel):
    """Safe, de-identified user and profile information for context.

    Never includes: password, password_hash, tokens, or secrets.
    """

    user_id: int
    display_name: str
    persona: str
    currency: str
    country: str
    risk_profile: Optional[str] = None


# ---------------------------------------------------------------------------
# Cash Flow
# ---------------------------------------------------------------------------


class CashFlowSummary(BaseModel):
    """Cash flow aggregation for the dashboard period."""

    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    savings: Decimal
    savings_rate_percent: Optional[Decimal] = Field(
        default=None,
        description="None when income is zero or unavailable.",
    )
    income_by_category: Dict[str, Decimal] = Field(default_factory=dict)
    expense_by_category: Dict[str, Decimal] = Field(default_factory=dict)
    has_data: bool = Field(
        default=False,
        description="False when user has no income or expense records.",
    )


# ---------------------------------------------------------------------------
# Net Worth
# ---------------------------------------------------------------------------


class NetWorthSummary(BaseModel):
    """Balance sheet snapshot using stored asset and liability values."""

    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    liquid_assets: Decimal
    assets_by_type: Dict[str, Decimal] = Field(default_factory=dict)
    liabilities_by_type: Dict[str, Decimal] = Field(default_factory=dict)
    has_data: bool = Field(
        default=False,
        description="False when user has no asset or liability records.",
    )


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------


class InvestmentSummary(BaseModel):
    """Portfolio aggregation using stored investment values (no live prices)."""

    total_invested: Decimal
    current_value: Decimal
    total_gain_loss: Decimal
    total_return_percentage: Decimal
    allocation_by_type: Dict[str, Decimal] = Field(default_factory=dict)
    allocation_percentages: Dict[str, Decimal] = Field(default_factory=dict)
    investment_count: int
    has_data: bool = Field(
        default=False,
        description="False when user has no investment records.",
    )


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------


class LoanContextItem(BaseModel):
    """Summary of a single loan record."""

    id: int
    loan_type: str
    lender: str
    principal_amount: Decimal
    outstanding_amount: Decimal
    emi: Optional[Decimal] = None
    interest_rate_percent: Decimal = Field(
        description="Annual interest rate as percentage, e.g. 8.75."
    )
    status: str


class LoanSummary(BaseModel):
    """Aggregated loan context across all user loans."""

    total_outstanding: Decimal
    total_principal: Decimal
    total_monthly_emi: Decimal
    loan_count: int
    active_loan_count: int
    loans: List[LoanContextItem] = Field(default_factory=list)
    has_data: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Debt
# ---------------------------------------------------------------------------


class DebtSummary(BaseModel):
    """Debt metrics derived from liabilities and loans.

    ``dti_percent`` is None when monthly income is zero — dividing by zero
    would produce a meaningless result.  The frontend/AI must handle this
    case explicitly rather than treating it as 0 %.
    """

    total_debt: Decimal
    monthly_obligations: Decimal
    dti_percent: Optional[Decimal] = Field(
        default=None,
        description="Debt-to-income ratio percentage. None = insufficient income data.",
    )
    has_data: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


class GoalContextItem(BaseModel):
    """Progress summary for a single financial goal."""

    id: int
    name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    completion_percentage: Decimal
    target_date: Optional[date] = None
    status: str
    required_monthly_contribution: Optional[Decimal] = None


class GoalSummary(BaseModel):
    """Aggregated goal progress context."""

    total_goals: int
    active_count: int
    completed_count: int
    goals: List[GoalContextItem] = Field(default_factory=list)
    has_data: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------


class BudgetSummary(BaseModel):
    """Budget adherence aggregation."""

    total_budget: Decimal
    total_spending: Decimal
    remaining_budget: Decimal
    overall_utilization_percent: Decimal
    over_budget_categories: List[str] = Field(default_factory=list)
    has_data: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Financial Health
# ---------------------------------------------------------------------------


class FinancialHealthSummary(BaseModel):
    """Measurable financial health indicators.

    All fields are nullable — a field is None when the underlying data
    required to calculate it is unavailable.  This is intentionally not
    a single opaque score.

    Per AI_RULEBOOK.md and FINANCIAL_ENGINE.md this layer provides facts,
    not advice.  A future AI Advisor layer produces explanations.
    """

    savings_rate_percent: Optional[Decimal] = Field(
        default=None,
        description="None when income is zero.",
    )
    dti_percent: Optional[Decimal] = Field(
        default=None,
        description="Debt-to-income ratio. None when income is zero.",
    )
    emergency_fund_months: Optional[Decimal] = Field(
        default=None,
        description="Liquid savings / monthly essential expenses. None when expenses are zero.",
    )
    budget_utilization_percent: Optional[Decimal] = Field(
        default=None,
        description="Overall budget utilization. None when no budgets exist.",
    )
    goal_completion_rate_percent: Optional[Decimal] = Field(
        default=None,
        description="Percentage of goals marked COMPLETED. None when no goals exist.",
    )
    net_worth: Optional[Decimal] = Field(
        default=None,
        description="Total assets minus total liabilities. None when no asset/liability data.",
    )
    cash_flow_positive: Optional[bool] = Field(
        default=None,
        description="True when net cash flow > 0. None when no income/expense data.",
    )


# ---------------------------------------------------------------------------
# Top-level summary snapshot
# ---------------------------------------------------------------------------


class FinancialSummarySnapshot(BaseModel):
    """High-level financial snapshot for the dashboard header."""

    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    total_invested: Decimal
    total_debt: Decimal


# ---------------------------------------------------------------------------
# Top-level responses
# ---------------------------------------------------------------------------


class DashboardResponse(BaseModel):
    """Consolidated personalized financial dashboard response.

    This is the primary response type for GET /api/v1/dashboard.
    All sections use the same period, ensuring consistency.
    """

    context_version: str = Field(
        default="1",
        description="Schema version for future AI/RAG compatibility.",
    )
    period: PeriodInfo
    user: UserContextInfo
    summary: FinancialSummarySnapshot
    cash_flow: CashFlowSummary
    net_worth: NetWorthSummary
    investments: InvestmentSummary
    loans: LoanSummary
    debt: DebtSummary
    goals: GoalSummary
    budgets: BudgetSummary
    financial_health: FinancialHealthSummary


class FinancialContextResponse(BaseModel):
    """Machine-readable full financial context.

    Intended for: GET /api/v1/financial/context

    Structurally identical to DashboardResponse.  Future AI/RAG services
    call ``FinancialContextService`` directly (no HTTP hop) rather than
    consuming this endpoint — this endpoint is for direct frontend or
    diagnostic use only.
    """

    context_version: str = Field(default="1")
    period: PeriodInfo
    user: UserContextInfo
    summary: FinancialSummarySnapshot
    cash_flow: CashFlowSummary
    net_worth: NetWorthSummary
    investments: InvestmentSummary
    loans: LoanSummary
    debt: DebtSummary
    goals: GoalSummary
    budgets: BudgetSummary
    financial_health: FinancialHealthSummary
