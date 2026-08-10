"""
DhanSarthi Financial Engine — Financial Health Foundation Module.

Provides aggregate numerical financial metrics (savings rate, DTI, emergency fund
coverage, net worth, budget utilization, portfolio allocation) without producing
opaque or unexplainable arbitrary scores.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.financial.budget import analyze_budget
from app.financial.cash_flow import calculate_cash_flow
from app.financial.debt import analyze_debt
from app.financial.exceptions import InvalidFinancialInput
from app.financial.investments import analyze_portfolio
from app.financial.net_worth import calculate_net_worth
from app.financial.savings import calculate_savings
from app.financial.types import (
    BudgetAnalysisResult,
    CashFlowResult,
    DebtAnalysisResult,
    FinancialMetricsInput,
    FinancialMetricsResult,
    NetWorthResult,
    PortfolioSummaryResult,
    SavingsResult,
)


def calculate_emergency_fund_coverage(
    liquid_savings: Decimal, monthly_essential_expenses: Decimal
) -> Decimal | None:
    """
    Calculate emergency fund coverage in months.

    Formula:
        Coverage (Months) = Liquid Savings / Monthly Essential Expenses

    Args:
        liquid_savings: Easily accessible cash/liquid bank balance.
        monthly_essential_expenses: Monthly essential expense obligations.

    Returns:
        Decimal | None: Number of months covered, or None if essential expenses are zero/unknown.

    Raises:
        InvalidFinancialInput: If inputs are negative.
    """
    if liquid_savings < Decimal("0"):
        raise InvalidFinancialInput(
            f"Liquid savings cannot be negative: {liquid_savings}",
            details={"liquid_savings": str(liquid_savings)},
        )
    if monthly_essential_expenses < Decimal("0"):
        raise InvalidFinancialInput(
            f"Monthly essential expenses cannot be negative: {monthly_essential_expenses}",
            details={"monthly_essential_expenses": str(monthly_essential_expenses)},
        )

    if monthly_essential_expenses > Decimal("0"):
        raw_coverage = liquid_savings / monthly_essential_expenses
        return raw_coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return None


def calculate_financial_metrics(
    input_data: FinancialMetricsInput,
) -> FinancialMetricsResult:
    """
    Compute aggregate raw analytical financial metrics across all sub-engines.

    Args:
        input_data: FinancialMetricsInput payload.

    Returns:
        FinancialMetricsResult: Structured raw metrics bundle.
    """
    ref_date = input_data.reference_date or date.today()

    cf_res: CashFlowResult | None = None
    sav_res: SavingsResult | None = None
    if input_data.cash_flow_input is not None:
        cf_res = calculate_cash_flow(input_data.cash_flow_input)
        sav_res = calculate_savings(
            cf_res.total_income, cf_res.total_expenses, reference_date=ref_date
        )

    nw_res: NetWorthResult | None = None
    if input_data.net_worth_input is not None:
        nw_res = calculate_net_worth(input_data.net_worth_input)

    debt_res: DebtAnalysisResult | None = None
    if input_data.net_worth_input is not None:
        gross_inc = cf_res.total_income if cf_res else Decimal("0")
        debt_res = analyze_debt(
            liabilities=input_data.net_worth_input.liabilities,
            loans=input_data.loans,
            gross_monthly_income=gross_inc,
            reference_date=ref_date,
        )

    coverage_months: Decimal | None = None
    if nw_res is not None and input_data.monthly_essential_expenses is not None:
        coverage_months = calculate_emergency_fund_coverage(
            liquid_savings=nw_res.liquid_assets,
            monthly_essential_expenses=input_data.monthly_essential_expenses,
        )

    b_res: BudgetAnalysisResult | None = None
    if input_data.budget_input is not None:
        b_res = analyze_budget(input_data.budget_input)

    p_res: PortfolioSummaryResult | None = None
    if input_data.portfolio_input is not None:
        p_res = analyze_portfolio(input_data.portfolio_input)

    return FinancialMetricsResult(
        cash_flow=cf_res,
        savings=sav_res,
        net_worth=nw_res,
        debt=debt_res,
        emergency_fund_coverage_months=coverage_months,
        budget_summary=b_res,
        portfolio_summary=p_res,
        reference_date=ref_date,
    )
