"""
Deterministic Financial Signals Engine for DhanSarthi — Phase K.

Evaluates user financial health snapshots and metrics against authoritative,
transparent financial rules to produce actionable FinancialSignal objects.

Rule Categories:
  - HIGH_EXPENSE_RATIO (Expenses > 70% of monthly income)
  - LOW_SAVINGS_RATE (Savings rate < 20%)
  - HIGH_DEBT_BURDEN (Debt-to-Income DTI > 40%)
  - LOW_LIQUIDITY (Emergency fund coverage < 3 months)
  - GOAL_AT_RISK (Goal shortfall > 0 with < 6 months remaining)
  - HIGH_CONCENTRATION (Single asset class > 80% of investment portfolio)
  - EXCESS_IDLE_CASH (Liquid reserves > 12 months essential expenses)
  - BUDGET_OVERRUN (Overall budget utilization > 100%)
  - NEGATIVE_CASH_FLOW (Monthly expenses > income)
  - MISSING_EMERGENCY_FUND (Zero liquid reserves or missing coverage)
"""

from __future__ import annotations

import enum
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.financial.health_snapshot import FinancialHealthSnapshot


class FinancialSignalType(str, enum.Enum):
    """Categorization of financial health signals."""

    HIGH_EXPENSE_RATIO = "HIGH_EXPENSE_RATIO"
    LOW_SAVINGS_RATE = "LOW_SAVINGS_RATE"
    HIGH_DEBT_BURDEN = "HIGH_DEBT_BURDEN"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    GOAL_AT_RISK = "GOAL_AT_RISK"
    HIGH_CONCENTRATION = "HIGH_CONCENTRATION"
    EXCESS_IDLE_CASH = "EXCESS_IDLE_CASH"
    BUDGET_OVERRUN = "BUDGET_OVERRUN"
    NEGATIVE_CASH_FLOW = "NEGATIVE_CASH_FLOW"
    MISSING_EMERGENCY_FUND = "MISSING_EMERGENCY_FUND"


class SignalSeverity(str, enum.Enum):
    """Severity classification of financial signals."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FinancialSignal(BaseModel):
    """Deterministic financial rule signal payload."""

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    type: FinancialSignalType
    severity: SignalSeverity
    metric_name: str
    metric_value: Optional[str] = None
    title: str
    description: str
    evidence: str
    formula: Optional[str] = None


def evaluate_financial_signals(
    snapshot: FinancialHealthSnapshot,
) -> List[FinancialSignal]:
    """
    Evaluate deterministic signal rules over a user's FinancialHealthSnapshot.

    Args:
        snapshot: Authoritative FinancialHealthSnapshot.

    Returns:
        List[FinancialSignal]: Triggered deterministic signals ordered by severity.
    """
    signals: List[FinancialSignal] = []

    # Rule 1: NEGATIVE_CASH_FLOW
    if snapshot.savings.status == "NEGATIVE":
        sav_amt = snapshot.savings.savings_amount or Decimal("0")
        signals.append(
            FinancialSignal(
                type=FinancialSignalType.NEGATIVE_CASH_FLOW,
                severity=SignalSeverity.CRITICAL,
                metric_name="net_cash_flow",
                metric_value=f"₹{sav_amt:,.2f}",
                title="Negative Cash Flow Deficit",
                description="Your monthly expenses exceed your monthly income.",
                evidence=f"Net cash deficit of ₹{abs(sav_amt):,.2f} per month.",
                formula="Income - Expenses < 0",
            )
        )

    # Rule 2: LOW_SAVINGS_RATE
    if snapshot.savings.savings_rate_percent is not None:
        sr = snapshot.savings.savings_rate_percent
        if Decimal("0") <= sr < Decimal("15.0") and snapshot.savings.status != "NEGATIVE":
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.LOW_SAVINGS_RATE,
                    severity=SignalSeverity.HIGH if sr < Decimal("5.0") else SignalSeverity.MEDIUM,
                    metric_name="savings_rate_percent",
                    metric_value=f"{sr:.1f}%",
                    title="Low Savings Rate",
                    description="Your savings rate is below the recommended 20% benchmark.",
                    evidence=f"Current savings rate is {sr:.1f}%. Recommended range: 20–30%.",
                    formula="Savings / Income * 100",
                )
            )

    # Rule 3: HIGH_EXPENSE_RATIO
    if snapshot.expenses.expense_ratio_percent is not None:
        er = snapshot.expenses.expense_ratio_percent
        if er > Decimal("75.0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.HIGH_EXPENSE_RATIO,
                    severity=SignalSeverity.HIGH if er > Decimal("90.0") else SignalSeverity.MEDIUM,
                    metric_name="expense_ratio_percent",
                    metric_value=f"{er:.1f}%",
                    title="High Expense Ratio",
                    description="Monthly expenses consume a large portion of your monthly income.",
                    evidence=f"Expenses consume {er:.1f}% of income.",
                    formula="Expenses / Income * 100",
                )
            )

    # Rule 4: HIGH_DEBT_BURDEN
    if snapshot.debt.dti_percent is not None:
        dti = snapshot.debt.dti_percent
        if dti > Decimal("40.0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.HIGH_DEBT_BURDEN,
                    severity=SignalSeverity.CRITICAL if dti > Decimal("50.0") else SignalSeverity.HIGH,
                    metric_name="dti_percent",
                    metric_value=f"{dti:.1f}%",
                    title="Elevated Debt Burden (DTI)",
                    description="Your Debt-to-Income (DTI) ratio exceeds the standard 40% threshold.",
                    evidence=f"Monthly debt EMI commitments take up {dti:.1f}% of income.",
                    formula="Total Monthly EMI / Monthly Gross Income * 100",
                )
            )

    # Rule 5: LOW_LIQUIDITY & MISSING_EMERGENCY_FUND
    if snapshot.liquidity.coverage_months is not None:
        cov = snapshot.liquidity.coverage_months
        if cov == Decimal("0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.MISSING_EMERGENCY_FUND,
                    severity=SignalSeverity.CRITICAL,
                    metric_name="emergency_fund_coverage_months",
                    metric_value="0.0 months",
                    title="Missing Emergency Fund",
                    description="No liquid emergency reserves available for unexpected expenses.",
                    evidence="Liquid cash/bank reserves cover 0 months of essential expenses.",
                    formula="Liquid Savings / Monthly Essential Expenses",
                )
            )
        elif cov < Decimal("3.0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.LOW_LIQUIDITY,
                    severity=SignalSeverity.HIGH,
                    metric_name="emergency_fund_coverage_months",
                    metric_value=f"{cov:.1f} months",
                    title="Inadequate Emergency Reserves",
                    description="Emergency fund covers less than the standard 3-6 months benchmark.",
                    evidence=f"Current liquid reserves cover {cov:.1f} months of essential expenses.",
                    formula="Liquid Savings / Monthly Essential Expenses",
                )
            )
        elif cov > Decimal("12.0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.EXCESS_IDLE_CASH,
                    severity=SignalSeverity.LOW,
                    metric_name="emergency_fund_coverage_months",
                    metric_value=f"{cov:.1f} months",
                    title="Excess Idle Liquid Cash",
                    description="Holding significantly more than 12 months of essential expenses in liquid cash.",
                    evidence=f"Liquid cash covers {cov:.1f} months, which could be earning higher returns if invested.",
                    formula="Liquid Savings / Monthly Essential Expenses > 12",
                )
            )

    # Rule 6: HIGH_CONCENTRATION
    if snapshot.investments.status == "CONCENTRATED":
        alloc = snapshot.investments.allocation_percentages
        max_asset = max(alloc.items(), key=lambda x: x[1]) if alloc else ("Unknown", Decimal("0"))
        signals.append(
            FinancialSignal(
                type=FinancialSignalType.HIGH_CONCENTRATION,
                severity=SignalSeverity.MEDIUM,
                metric_name="investment_concentration_percent",
                metric_value=f"{max_asset[1]:.1f}%",
                title="Investment Portfolio Concentration",
                description=f"High concentration in {max_asset[0]}.",
                evidence=f"{max_asset[0]} accounts for {max_asset[1]:.1f}% of total portfolio value.",
                formula="Largest Asset Class Value / Total Portfolio Value * 100",
            )
        )

    # Rule 7: BUDGET_OVERRUN
    if snapshot.expenses.budget_utilization_percent is not None:
        b_util = snapshot.expenses.budget_utilization_percent
        if b_util > Decimal("100.0"):
            signals.append(
                FinancialSignal(
                    type=FinancialSignalType.BUDGET_OVERRUN,
                    severity=SignalSeverity.HIGH,
                    metric_name="budget_utilization_percent",
                    metric_value=f"{b_util:.1f}%",
                    title="Budget Utilization Exceeded",
                    description="Your overall spending has exceeded configured budget limits.",
                    evidence=f"Actual spending is at {b_util:.1f}% of total budget.",
                    formula="Total Actual Spending / Total Configured Budget * 100",
                )
            )

    # Sort signals by severity rank: CRITICAL > HIGH > MEDIUM > LOW > INFO
    severity_order = {
        SignalSeverity.CRITICAL: 0,
        SignalSeverity.HIGH: 1,
        SignalSeverity.MEDIUM: 2,
        SignalSeverity.LOW: 3,
        SignalSeverity.INFO: 4,
    }
    signals.sort(key=lambda s: severity_order.get(s.severity, 5))

    return signals
