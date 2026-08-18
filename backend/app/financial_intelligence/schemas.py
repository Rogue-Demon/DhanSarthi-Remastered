"""
Pydantic schemas representing structured analytical results, scenario models,
and consolidated intelligence summaries.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FinancialInsight(BaseModel):
    """Structured analysis evaluation for a specific financial dimension."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="ignore",
    )

    metric: str = Field(..., description="The name of the metric (e.g. 'net_cash_flow', 'savings_rate')")
    value: Any = Field(..., description="The computed numerical value or evaluation result")
    unit: str = Field(..., description="Unit of measurement (e.g. 'INR', '%', 'months', 'count')")
    status: str = Field(..., description="Classification status (e.g. 'POSITIVE', 'HEALTHY', 'LOW')")
    severity: str = Field(..., description="Severity level ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    period_days: Optional[int] = Field(default=None, description="Time period evaluated in days")
    data_sufficiency: str = Field(..., description="Data completeness status ('SUFFICIENT', 'PARTIAL', 'INSUFFICIENT')")
    explanation: str = Field(..., description="Developer-explainable formula basis or explanation")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Key inputs consumed by the calculation")
    formula: str = Field(..., description="The formula or mathematical logic representation")
    warnings: List[str] = Field(default_factory=list, description="Target warning flags raised in this area")


class FinancialIntelligenceSummary(BaseModel):
    """Consolidated financial summary containing analytical insights, alerts, and data quality."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="ignore",
    )

    cash_flow: FinancialInsight = Field(..., description="Structured net cash flow analysis")
    savings: FinancialInsight = Field(..., description="Structured savings and savings rate analysis")
    expenses: FinancialInsight = Field(..., description="Structured spending and concentration analysis")
    budget: FinancialInsight = Field(..., description="Structured budget utilization analysis")
    debt: FinancialInsight = Field(..., description="Structured debt burden and DTI analysis")
    emergency_fund: FinancialInsight = Field(..., description="Structured emergency fund coverage analysis")
    investments: FinancialInsight = Field(..., description="Structured portfolio allocation and returns analysis")
    goals: List[FinancialInsight] = Field(default_factory=list, description="Structured per-goal analyses")
    warnings: List[str] = Field(default_factory=list, description="Active warning alerts triggered by rules")
    opportunities: List[str] = Field(default_factory=list, description="Active opportunity recommendations triggered by rules")
    health_snapshot: Optional[Any] = Field(default=None, description="Presentation-independent FinancialHealthSnapshot")
    signals: List[Any] = Field(default_factory=list, description="Deterministic financial rule signals")
    data_quality: str = Field(..., description="Consolidated data quality status ('COMPLETE', 'GOOD', 'PARTIAL', 'LIMITED')")
    data_as_of: str = Field(..., description="Valuation timestamp or data freshness date (ISO-8601)")


class LoanScenarioInput(BaseModel):
    """Input parameters for proposed loan affordability simulation."""

    model_config = ConfigDict(extra="forbid")

    principal: Decimal = Field(..., ge=0, description="Proposed loan principal amount")
    annual_interest_rate_percent: Decimal = Field(..., ge=0, description="Annual interest rate percentage")
    tenure_months: int = Field(..., ge=1, description="Loan repayment duration in months")


class LoanScenarioResult(BaseModel):
    """Outputs for proposed loan affordability simulation."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    emi: Decimal = Field(..., description="Simulated monthly EMI obligation")
    total_repayment: Decimal = Field(..., description="Simulated total principal + interest repayment")
    total_interest: Decimal = Field(..., description="Simulated total interest component paid")
    post_loan_dti: Optional[Decimal] = Field(..., description="Simulated post-loan Debt-to-Income percentage")
    post_loan_surplus: Decimal = Field(..., description="Simulated monthly surplus remaining after proposed EMI")
    post_loan_cash_flow_status: str = Field(..., description="Simulated monthly cash flow state ('POSITIVE', 'BREAK_EVEN', 'NEGATIVE')")
    risk_flags: List[str] = Field(default_factory=list, description="Simulated risk warning flags triggered by loan parameters")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Key parameters and compounding frequency assumed")
    limitations: str = Field(..., description="Disclaimer regarding licensed underwriting and rate fluctuations")


class GenericScenarioInput(BaseModel):
    """Generic input format for savings, compound growth, and goal adjustments."""

    model_config = ConfigDict(extra="forbid")

    scenario_type: str = Field(..., description="Type of scenario: 'SAVINGS', 'INVESTMENT_GROWTH', 'GOAL_CONTRIBUTION'")
    params: Dict[str, Any] = Field(..., description="Type-specific configuration values")


class GenericScenarioResult(BaseModel):
    """Generic baseline vs simulated comparison result."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    base_value: Decimal = Field(..., description="Existing metric baseline value")
    scenario_value: Decimal = Field(..., description="Simulated scenario value")
    difference: Decimal = Field(..., description="Net variance between baseline and scenario values")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Compounding, time, or rate assumptions")
    limitations: str = Field(..., description="Scenario limitations and lack of pricing guarantees disclaimer")
