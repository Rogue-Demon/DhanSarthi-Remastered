"""
Domain input and result types for DhanSarthi Financial Engine.

All monetary amounts, rates, percentages, and financial metrics use
``decimal.Decimal`` to guarantee numerical precision and avoid binary
floating-point inaccuracies.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AssetType,
    BudgetPeriod,
    ExpenseFrequency,
    IncomeFrequency,
    InvestmentType,
    LiabilityType,
    LoanType,
)

# Shared Config for all financial types
_FINANCIAL_TYPE_CONFIG = ConfigDict(
    arbitrary_types_allowed=True,
    validate_assignment=True,
    extra="forbid",
)


# ============================================================================
# INPUT TYPES
# ============================================================================


class IncomeItemInput(BaseModel):
    """Input representing a single income record."""

    model_config = _FINANCIAL_TYPE_CONFIG

    amount: Decimal = Field(..., description="Income amount")
    category: str = Field(..., description="Category of income")
    frequency: IncomeFrequency | str = Field(
        default=IncomeFrequency.MONTHLY, description="Recurrence frequency"
    )
    source: Optional[str] = Field(default=None, description="Optional income source")
    is_recurring: bool = Field(default=True, description="Whether recurring")


class ExpenseItemInput(BaseModel):
    """Input representing a single expense record."""

    model_config = _FINANCIAL_TYPE_CONFIG

    amount: Decimal = Field(..., description="Expense amount")
    category: str = Field(..., description="Category of expense")
    frequency: ExpenseFrequency | str = Field(
        default=ExpenseFrequency.MONTHLY, description="Recurrence frequency"
    )
    is_essential: bool = Field(
        default=False, description="Whether expense is essential"
    )
    source: Optional[str] = Field(default=None, description="Optional expense description")


class CashFlowInput(BaseModel):
    """Input payload for cash flow and savings calculations."""

    model_config = _FINANCIAL_TYPE_CONFIG

    incomes: List[IncomeItemInput] = Field(default_factory=list)
    expenses: List[ExpenseItemInput] = Field(default_factory=list)
    period_days: Optional[int] = Field(default=None, description="Optional calculation period in days")
    reference_date: Optional[date] = Field(default=None, description="Calculation reference date")


class AssetItemInput(BaseModel):
    """Input representing a user-owned asset."""

    model_config = _FINANCIAL_TYPE_CONFIG

    name: str
    asset_type: AssetType | str
    current_value: Decimal
    is_liquid: bool = Field(default=False, description="Whether easily convertable to cash")


class LiabilityItemInput(BaseModel):
    """Input representing a user financial liability."""

    model_config = _FINANCIAL_TYPE_CONFIG

    name: str
    liability_type: LiabilityType | str
    outstanding_balance: Decimal
    monthly_payment: Decimal = Field(default=Decimal("0"))


class NetWorthInput(BaseModel):
    """Input payload for Net Worth and balance sheet analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    assets: List[AssetItemInput] = Field(default_factory=list)
    liabilities: List[LiabilityItemInput] = Field(default_factory=list)
    reference_date: Optional[date] = Field(default=None)


class LoanInput(BaseModel):
    """Input parameters for loan calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    principal: Decimal = Field(..., description="Loan principal amount")
    annual_interest_rate_percent: Decimal = Field(..., description="Annual interest rate percentage")
    tenure_months: int = Field(..., description="Tenure in months")
    loan_type: Optional[LoanType | str] = Field(default=None)
    payment_frequency: str = Field(default="MONTHLY")


class LoanAffordabilityInput(BaseModel):
    """Input payload for evaluating loan affordability."""

    model_config = _FINANCIAL_TYPE_CONFIG

    monthly_income: Decimal
    monthly_expenses: Decimal
    existing_monthly_emi: Decimal
    proposed_loan: LoanInput
    liquid_savings: Optional[Decimal] = Field(default=None)


class SIPInput(BaseModel):
    """Input parameters for Systematic Investment Plan (SIP) projection."""

    model_config = _FINANCIAL_TYPE_CONFIG

    monthly_contribution: Decimal
    expected_annual_return_percent: Decimal
    duration_years: Decimal
    contribution_frequency: str = Field(default="MONTHLY")


class CompoundingInput(BaseModel):
    """Input parameters for generic compound growth calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    principal: Decimal
    periodic_contribution: Decimal = Field(default=Decimal("0"))
    annual_rate_percent: Decimal
    compounding_frequency_per_year: int = Field(default=12)
    duration_years: Decimal


class InvestmentItemInput(BaseModel):
    """Input representing an individual investment holding."""

    model_config = _FINANCIAL_TYPE_CONFIG

    name: str
    investment_type: InvestmentType | str
    invested_amount: Decimal
    current_value: Decimal
    purchase_date: Optional[date] = Field(default=None)
    units: Optional[Decimal] = Field(default=None)


class PortfolioInput(BaseModel):
    """Input payload for investment portfolio analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    investments: List[InvestmentItemInput] = Field(default_factory=list)
    reference_date: Optional[date] = Field(default=None)


class GoalInput(BaseModel):
    """Input payload for financial goal progress analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    title: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    expected_annual_return_percent: Decimal = Field(default=Decimal("0"))
    reference_date: Optional[date] = Field(default=None)


class BudgetCategoryInput(BaseModel):
    """Input budget and spending for a single category."""

    model_config = _FINANCIAL_TYPE_CONFIG

    category: str
    budget_amount: Decimal
    actual_spending: Decimal


class BudgetAnalysisInput(BaseModel):
    """Input payload for overall budget analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    category_budgets: List[BudgetCategoryInput] = Field(default_factory=list)
    period: BudgetPeriod | str = Field(default=BudgetPeriod.MONTHLY)


class FinancialMetricsInput(BaseModel):
    """Input payload for consolidated raw financial health metrics calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    cash_flow_input: Optional[CashFlowInput] = None
    net_worth_input: Optional[NetWorthInput] = None
    loans: Optional[List[LoanInput]] = None
    portfolio_input: Optional[PortfolioInput] = None
    budget_input: Optional[BudgetAnalysisInput] = None
    monthly_essential_expenses: Optional[Decimal] = None
    reference_date: Optional[date] = None


# ============================================================================
# RESULT TYPES
# ============================================================================


class CashFlowResult(BaseModel):
    """Result structure for cash flow analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    income_by_category: Dict[str, Decimal]
    expense_by_category: Dict[str, Decimal]
    top_expense_categories: List[Tuple[str, Decimal]]
    period_days: Optional[int] = None
    reference_date: date


class SavingsResult(BaseModel):
    """Result structure for savings analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal
    savings_rate_percent: Optional[Decimal]
    is_income_zero: bool
    reference_date: date


class NetWorthResult(BaseModel):
    """Result structure for net worth calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    liquid_assets: Decimal
    illiquid_assets: Decimal
    assets_by_type: Dict[str, Decimal]
    liabilities_by_type: Dict[str, Decimal]
    reference_date: date


class DebtAnalysisResult(BaseModel):
    """Result structure for debt metrics."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_liabilities_balance: Decimal
    total_monthly_emi: Decimal
    dti_percent: Optional[Decimal]
    reference_date: date


class AmortizationScheduleEntry(BaseModel):
    """Entry for a single payment period in an loan amortization schedule."""

    model_config = _FINANCIAL_TYPE_CONFIG

    payment_number: int
    opening_balance: Decimal
    emi: Decimal
    principal_component: Decimal
    interest_component: Decimal
    closing_balance: Decimal


class LoanCalculationResult(BaseModel):
    """Result structure for loan EMI and amortization calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    principal: Decimal
    annual_interest_rate_percent: Decimal
    tenure_months: int
    emi: Decimal
    total_repayment: Decimal
    total_interest: Decimal
    amortization_schedule: Optional[List[AmortizationScheduleEntry]] = None
    assumptions: Dict[str, Any]


class LoanAffordabilityResult(BaseModel):
    """Result structure for loan affordability analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    proposed_emi: Decimal
    total_monthly_income: Decimal
    existing_monthly_debt: Decimal
    new_total_monthly_debt: Decimal
    current_dti_percent: Optional[Decimal]
    proposed_dti_percent: Optional[Decimal]
    net_monthly_cash_flow_after_loan: Decimal
    metrics: Dict[str, Any]


class SIPCalculationResult(BaseModel):
    """Result structure for SIP calculations."""

    model_config = _FINANCIAL_TYPE_CONFIG

    monthly_contribution: Decimal
    expected_annual_return_percent: Decimal
    duration_years: Decimal
    total_invested: Decimal
    estimated_future_value: Decimal
    estimated_gains: Decimal
    assumptions: Dict[str, Any]


class CompoundingResult(BaseModel):
    """Result structure for generic compound growth calculation."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_invested: Decimal
    future_value: Decimal
    interest_earned: Decimal
    assumptions: Dict[str, Any]


class InvestmentReturnResult(BaseModel):
    """Result structure for individual investment performance."""

    model_config = _FINANCIAL_TYPE_CONFIG

    name: str
    invested_amount: Decimal
    current_value: Decimal
    gain_loss: Decimal
    return_percentage: Decimal
    absolute_return: Decimal


class PortfolioSummaryResult(BaseModel):
    """Result structure for investment portfolio analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_invested: Decimal
    current_value: Decimal
    total_gain_loss: Decimal
    total_return_percentage: Decimal
    allocation_by_type: Dict[str, Decimal]
    allocation_percentages: Dict[str, Decimal]


class GoalAnalysisResult(BaseModel):
    """Result structure for financial goal tracking."""

    model_config = _FINANCIAL_TYPE_CONFIG

    title: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    time_remaining_months: int
    completion_percentage: Decimal
    required_monthly_contribution: Optional[Decimal]
    shortfall: Decimal
    is_completed: bool
    assumptions: Dict[str, Any]


class BudgetCategoryResult(BaseModel):
    """Result structure for single budget category analysis."""

    model_config = _FINANCIAL_TYPE_CONFIG

    category: str
    budget_amount: Decimal
    actual_spending: Decimal
    remaining_budget: Decimal
    utilization_percentage: Decimal
    is_over_budget: bool
    over_budget_amount: Decimal


class BudgetAnalysisResult(BaseModel):
    """Result structure for overall budget performance."""

    model_config = _FINANCIAL_TYPE_CONFIG

    total_budget: Decimal
    total_spending: Decimal
    total_remaining: Decimal
    overall_utilization_percentage: Decimal
    category_results: List[BudgetCategoryResult]
    over_budget_categories: List[str]


class FinancialMetricsResult(BaseModel):
    """Result structure for aggregate financial health metrics."""

    model_config = _FINANCIAL_TYPE_CONFIG

    cash_flow: Optional[CashFlowResult] = None
    savings: Optional[SavingsResult] = None
    net_worth: Optional[NetWorthResult] = None
    debt: Optional[DebtAnalysisResult] = None
    emergency_fund_coverage_months: Optional[Decimal] = None
    budget_summary: Optional[BudgetAnalysisResult] = None
    portfolio_summary: Optional[PortfolioSummaryResult] = None
    reference_date: date
