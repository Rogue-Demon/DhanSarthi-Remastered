"""
Report Data Generator for DhanSarthi.

Transforms authoritative FinancialContext and underlying domain entities
into a structured, presentation-agnostic report data model.
Zero financial business logic is duplicated here.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from app.models.enums import GoalStatus, FinancialReportType
from app.reports.enums import ReportType

if TYPE_CHECKING:
    from app.services.financial_context_service import FinancialContext


class ReportKPI(BaseModel):
    """A single high-level key performance metric."""
    label: str
    value: str
    subtext: Optional[str] = None


class ReportTable(BaseModel):
    """A tabular dataset within a report."""
    title: str
    headers: List[str]
    rows: List[List[Any]]
    totals: Optional[List[str]] = None


class ReportData(BaseModel):
    """Presentation-agnostic structured report payload."""
    report_type: ReportType
    title: str
    user_name: str
    user_email: str
    period_start: str
    period_end: str
    generated_at: str
    summary_kpis: List[ReportKPI] = Field(default_factory=list)
    tables: List[ReportTable] = Field(default_factory=list)
    footnotes: List[str] = Field(default_factory=list)
    data_freshness: str = "Live authoritative database snapshot"


def _fmt_curr(val: Any) -> str:
    """Helper to format currency strings with Indian comma notation or standard fallback."""
    if val is None:
        return "₹0.00"
    try:
        dec = Decimal(str(val))
        return f"₹{dec:,.2f}"
    except Exception:
        return str(val)


class ReportDataGenerator:
    """Generates structured ReportData instances from FinancialContext."""

    @staticmethod
    def generate(
        ctx: Optional[FinancialContext] = None,
        report_type: Any = ReportType.FINANCIAL_SUMMARY,
        period_start: Optional[Any] = None,
        period_end: Optional[Any] = None,
        context: Optional[FinancialContext] = None,
    ) -> ReportData:
        ctx = context or ctx
        if ctx is None:
            raise ValueError("FinancialContext must be provided to ReportDataGenerator.generate")

        user_name = getattr(ctx.profile, "display_name", None) or getattr(ctx.profile, "full_name", None) or "Valued Member"
        user_email = getattr(ctx.profile, "email", "") or f"user_{ctx.user_id}@dhansarthi.local"
        p_start = (period_start or ctx.period_start).isoformat()
        p_end = (period_end or ctx.period_end).isoformat()
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")

        # Map enum string or instance to ReportType
        rtype_str = str(getattr(report_type, "value", report_type)).lower()

        type_mapping = {
            "financial_summary": ReportType.FINANCIAL_SUMMARY,
            "monthly_executive": ReportType.MONTHLY_FINANCIAL_REPORT,
            "annual_tax_summary": ReportType.ANNUAL_REPORT,
            "annual_report": ReportType.ANNUAL_REPORT,
            "expense_breakdown": ReportType.INCOME_EXPENSE,
            "income_expense": ReportType.INCOME_EXPENSE,
            "net_worth_statement": ReportType.FINANCIAL_SUMMARY,
            "cash_flow": ReportType.CASH_FLOW,
            "budget": ReportType.BUDGET,
            "goal_feasibility": ReportType.GOALS,
            "goals": ReportType.GOALS,
            "debt_snowball": ReportType.LIABILITIES,
            "liabilities": ReportType.LIABILITIES,
            "investments": ReportType.INVESTMENTS,
        }

        resolved_type = type_mapping.get(rtype_str, ReportType.FINANCIAL_SUMMARY)

        dispatch = {
            ReportType.FINANCIAL_SUMMARY: ReportDataGenerator._build_financial_summary,
            ReportType.CASH_FLOW: ReportDataGenerator._build_cash_flow,
            ReportType.INCOME_EXPENSE: ReportDataGenerator._build_income_expense,
            ReportType.BUDGET: ReportDataGenerator._build_budget,
            ReportType.GOALS: ReportDataGenerator._build_goals,
            ReportType.INVESTMENTS: ReportDataGenerator._build_investments,
            ReportType.LIABILITIES: ReportDataGenerator._build_liabilities,
            ReportType.MONTHLY_FINANCIAL_REPORT: ReportDataGenerator._build_financial_summary,
            ReportType.ANNUAL_REPORT: ReportDataGenerator._build_financial_summary,
        }

        builder = dispatch.get(resolved_type, ReportDataGenerator._build_financial_summary)
        return builder(ctx, resolved_type, user_name, user_email, p_start, p_end, now_str)

    @staticmethod
    def _build_financial_summary(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        nw = ctx.metrics.net_worth if ctx.metrics else None
        cf = ctx.metrics.cash_flow if ctx.metrics else None
        sav = ctx.metrics.savings if ctx.metrics else None

        net_worth_val = nw.net_worth if nw else Decimal("0")
        total_assets_val = nw.total_assets if nw else Decimal("0")
        total_liabilities_val = nw.total_liabilities if nw else Decimal("0")
        net_cash_flow_val = cf.net_cash_flow if cf else Decimal("0")
        savings_rate_val = sav.savings_rate_percent if sav and sav.savings_rate_percent is not None else Decimal("0")

        kpis = [
            ReportKPI(label="Net Worth", value=_fmt_curr(net_worth_val), subtext="Total Assets − Liabilities"),
            ReportKPI(label="Total Assets", value=_fmt_curr(total_assets_val), subtext="Cumulative asset valuation"),
            ReportKPI(label="Total Liabilities", value=_fmt_curr(total_liabilities_val), subtext="Outstanding debt obligations"),
            ReportKPI(label="Net Cash Flow", value=_fmt_curr(net_cash_flow_val), subtext=f"Savings rate: {savings_rate_val:.1f}%"),
        ]

        summary_table = ReportTable(
            title="Executive Financial Snapshot",
            headers=["Financial Metric", "Amount (INR)", "Context / Status"],
            rows=[
                ["Net Worth", _fmt_curr(net_worth_val), "Assets minus Liabilities"],
                ["Total Assets", _fmt_curr(total_assets_val), "All liquid & illiquid assets"],
                ["Total Liabilities", _fmt_curr(total_liabilities_val), "Total active debt"],
                ["Net Cash Flow", _fmt_curr(net_cash_flow_val), f"Net periodic inflow"],
                ["Savings Rate", f"{savings_rate_val:.1f}%", "Percentage of income saved"],
            ]
        )

        title = "Annual Financial Statement" if report_type == ReportType.ANNUAL_REPORT else "Executive Financial Summary"

        return ReportData(
            report_type=report_type,
            title=title,
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[summary_table],
            footnotes=["All valuations calculated in INR based on authoritative database metrics."]
        )

    @staticmethod
    def _build_cash_flow(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        cf = ctx.metrics.cash_flow if ctx.metrics else None
        sav = ctx.metrics.savings if ctx.metrics else None

        total_income = cf.total_income if cf else Decimal("0")
        total_expenses = cf.total_expenses if cf else Decimal("0")
        net_cash_flow = cf.net_cash_flow if cf else Decimal("0")
        savings_rate = sav.savings_rate_percent if sav and sav.savings_rate_percent is not None else Decimal("0")

        kpis = [
            ReportKPI(label="Total Inflow (Income)", value=_fmt_curr(total_income)),
            ReportKPI(label="Total Outflow (Expenses)", value=_fmt_curr(total_expenses)),
            ReportKPI(label="Net Cash Flow", value=_fmt_curr(net_cash_flow)),
            ReportKPI(label="Savings Rate", value=f"{savings_rate:.1f}%"),
        ]


        table = ReportTable(
            title="Cash Flow Summary",
            headers=["Component", "Period Total", "Notes"],
            rows=[
                ["Total Income Inflow", _fmt_curr(total_income), "All income sources"],
                ["Total Expense Outflow", _fmt_curr(total_expenses), "All recorded expenses"],
                ["Net Surplus / Deficit", _fmt_curr(net_cash_flow), "Inflow minus Outflow"],
                ["Periodic Savings Rate", f"{savings_rate:.1f}%", "Saved income ratio"],
            ]
        )

        return ReportData(
            report_type=report_type,
            title="Cash Flow & Liquidity Report",
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[table],
            footnotes=["Periodic cash flows reflect reconciled entries within the active reporting window."]
        )

    @staticmethod
    def _build_income_expense(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        return ReportDataGenerator._build_cash_flow(ctx, report_type, user_name, user_email, p_start, p_end, now_str)

    @staticmethod
    def _build_budget(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        bs = ctx.metrics.budget_summary if ctx.metrics else None

        total_limit = bs.total_budget if bs else Decimal("0")
        total_spend = bs.total_spending if bs else Decimal("0")
        total_remaining = bs.total_remaining if bs else Decimal("0")
        overall_util = bs.overall_utilization_percentage if bs else Decimal("0")

        rows = []
        if bs and bs.category_results:
            for cat_res in bs.category_results:
                rows.append([
                    cat_res.category,
                    _fmt_curr(cat_res.budget_amount),
                    _fmt_curr(cat_res.actual_spending),
                    _fmt_curr(cat_res.remaining),
                    f"{cat_res.utilization_percentage:.1f}%"
                ])

        kpis = [
            ReportKPI(label="Total Budget Limit", value=_fmt_curr(total_limit)),
            ReportKPI(label="Actual Total Spend", value=_fmt_curr(total_spend)),
            ReportKPI(label="Total Remaining", value=_fmt_curr(total_remaining)),
            ReportKPI(label="Overall Utilization", value=f"{overall_util:.1f}%"),
        ]

        table = ReportTable(
            title="Budget Utilization by Category",
            headers=["Category", "Budget Limit", "Actual Spend", "Remaining", "Utilization %"],
            rows=rows,
            totals=["Total", _fmt_curr(total_limit), _fmt_curr(total_spend), _fmt_curr(total_remaining), f"{overall_util:.1f}%"]
        )

        return ReportData(
            report_type=report_type,
            title="Budget Performance & Variance Report",
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[table],
            footnotes=["Budget thresholds and variances derived from authenticated user budgets."]
        )

    @staticmethod
    def _build_goals(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        rows = []
        total_target = Decimal("0.00")
        total_current = Decimal("0.00")

        for goal, analysis in ctx.goal_analyses:
            target = goal.target_amount or Decimal("0")
            curr = goal.current_amount or Decimal("0")
            rem = max(Decimal("0.00"), target - curr)
            prog = (curr / target * Decimal("100")) if target > 0 else Decimal("0")
            total_target += target
            total_current += curr
            rows.append([
                goal.name or "Goal",
                goal.target_date.isoformat() if goal.target_date else "-",
                _fmt_curr(target),
                _fmt_curr(curr),
                _fmt_curr(rem),
                f"{prog:.1f}%"
            ])

        overall_prog = (total_current / total_target * Decimal("100")) if total_target > 0 else Decimal("0")

        kpis = [
            ReportKPI(label="Total Target Required", value=_fmt_curr(total_target)),
            ReportKPI(label="Total Amount Saved", value=_fmt_curr(total_current)),
            ReportKPI(label="Remaining Funding Gap", value=_fmt_curr(total_target - total_current)),
            ReportKPI(label="Overall Progress", value=f"{overall_prog:.1f}%"),
        ]

        table = ReportTable(
            title="Active Financial Goals Tracking",
            headers=["Goal Name", "Target Date", "Target Amount", "Current Saved", "Remaining Gap", "Progress %"],
            rows=rows,
            totals=["Total", "", _fmt_curr(total_target), _fmt_curr(total_current), _fmt_curr(total_target - total_current), f"{overall_prog:.1f}%"]
        )

        return ReportData(
            report_type=report_type,
            title="Financial Goals & Milestones Report",
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[table],
            footnotes=["Goal tracking progress assumes ongoing disciplined contributions."]
        )

    @staticmethod
    def _build_investments(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        ps = ctx.metrics.portfolio_summary if ctx.metrics else None

        total_invested = ps.total_invested if ps else Decimal("0")
        total_current = ps.total_current_value if ps else Decimal("0")
        total_pnl = ps.total_pnl if ps else Decimal("0")
        pnl_percent = ps.total_pnl_percentage if ps else Decimal("0")

        kpis = [
            ReportKPI(label="Total Invested Cost", value=_fmt_curr(total_invested)),
            ReportKPI(label="Current Portfolio Value", value=_fmt_curr(total_current)),
            ReportKPI(label="Total Unrealized P&L", value=_fmt_curr(total_pnl)),
            ReportKPI(label="Portfolio Return", value=f"{pnl_percent:.2f}%"),
        ]

        table = ReportTable(
            title="Portfolio Summary",
            headers=["Metric", "Amount (INR)", "Return %"],
            rows=[
                ["Invested Principal", _fmt_curr(total_invested), "-"],
                ["Current Portfolio Valuation", _fmt_curr(total_current), f"{pnl_percent:.2f}%"],
                ["Total Net Profit / Loss", _fmt_curr(total_pnl), f"{pnl_percent:.2f}%"],
            ]
        )

        return ReportData(
            report_type=report_type,
            title="Investment Portfolio Valuation Report",
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[table],
            footnotes=["Valuations reflect latest market price calculations."]
        )

    @staticmethod
    def _build_liabilities(
        ctx: FinancialContext,
        report_type: ReportType,
        user_name: str,
        user_email: str,
        p_start: str,
        p_end: str,
        now_str: str,
    ) -> ReportData:
        nw = ctx.metrics.net_worth if ctx.metrics else None
        debt_metrics = ctx.metrics.debt if ctx.metrics else None

        total_debt = nw.total_liabilities if nw else Decimal("0")

        rows = []
        for loan in ctx.loans:
            rows.append([
                loan.lender_name or "Loan",
                loan.loan_type.value if hasattr(loan.loan_type, "value") else str(loan.loan_type),
                f"{loan.interest_rate * Decimal('100'):.2f}%" if loan.interest_rate else "-",
                _fmt_curr(loan.principal_amount)
            ])

        kpis = [
            ReportKPI(label="Total Outstanding Debt", value=_fmt_curr(total_debt)),
            ReportKPI(label="Active Loans Count", value=str(len(ctx.loans))),
            ReportKPI(label="Debt to Income Ratio", value=f"{debt_metrics.debt_to_income_ratio:.1f}%" if debt_metrics and debt_metrics.debt_to_income_ratio is not None else "-"),
        ]

        table = ReportTable(
            title="Liabilities & Loans Schedule",
            headers=["Lender / Institution", "Category", "Interest Rate", "Principal Amount"],
            rows=rows,
            totals=["Total Outstanding", "", "", _fmt_curr(total_debt)]
        )

        return ReportData(
            report_type=report_type,
            title="Liabilities & Debt Analysis Report",
            user_name=user_name,
            user_email=user_email,
            period_start=p_start,
            period_end=p_end,
            generated_at=now_str,
            summary_kpis=kpis,
            tables=[table],
            footnotes=["Debt metrics reflect recorded loans and liabilities in the DhanSarthi engine."]
        )
