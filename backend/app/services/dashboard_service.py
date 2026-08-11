"""
Dashboard Service for DhanSarthi — Phase 8.

Thin orchestrator that converts a ``FinancialContext`` (produced by
``FinancialContextService``) into the structured Pydantic schemas consumed
by the API layer.

Responsibilities:
  - Call FinancialContextService.build_context()
  - Map FinancialContext → DashboardResponse / FinancialContextResponse
  - Handle missing-data sentinel values (None vs 0)

This service performs NO financial calculations.
All arithmetic belongs to the Financial Engine.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import GoalStatus, LoanStatus
from app.schemas.dashboard import (
    BudgetSummary,
    CashFlowSummary,
    DashboardResponse,
    DebtSummary,
    FinancialContextResponse,
    FinancialHealthSummary,
    FinancialSummarySnapshot,
    GoalContextItem,
    GoalSummary,
    InvestmentSummary,
    LoanContextItem,
    LoanSummary,
    NetWorthSummary,
    PeriodInfo,
    UserContextInfo,
)
from app.services.financial_context_service import FinancialContext, FinancialContextService


class DashboardService:
    """
    Assembles the dashboard response from a single FinancialContext build.

    Call chain:
        API route
          ↓
        DashboardService.build_dashboard(user_id, date_from, date_to)
          ↓
        FinancialContextService.build_context(...)
          ↓
        _map_to_response(context)
          ↓
        DashboardResponse
    """

    def __init__(self, db: Session) -> None:
        self._context_svc = FinancialContextService(db)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def build_dashboard(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardResponse:
        """Build the consolidated dashboard response for the authenticated user."""
        context = self._context_svc.build_context(user_id, date_from=date_from, date_to=date_to)
        return self._map_to_dashboard_response(context)

    def build_financial_context(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> FinancialContextResponse:
        """Build the machine-readable financial context response."""
        context = self._context_svc.build_context(user_id, date_from=date_from, date_to=date_to)
        return self._map_to_context_response(context)

    # ------------------------------------------------------------------
    # Internal mapping helpers
    # ------------------------------------------------------------------

    def _map_to_dashboard_response(self, ctx: FinancialContext) -> DashboardResponse:
        sections = self._build_sections(ctx)
        return DashboardResponse(
            period=sections["period"],
            user=sections["user"],
            summary=sections["summary"],
            cash_flow=sections["cash_flow"],
            net_worth=sections["net_worth"],
            investments=sections["investments"],
            loans=sections["loans"],
            debt=sections["debt"],
            goals=sections["goals"],
            budgets=sections["budgets"],
            financial_health=sections["financial_health"],
        )

    def _map_to_context_response(self, ctx: FinancialContext) -> FinancialContextResponse:
        sections = self._build_sections(ctx)
        return FinancialContextResponse(
            period=sections["period"],
            user=sections["user"],
            summary=sections["summary"],
            cash_flow=sections["cash_flow"],
            net_worth=sections["net_worth"],
            investments=sections["investments"],
            loans=sections["loans"],
            debt=sections["debt"],
            goals=sections["goals"],
            budgets=sections["budgets"],
            financial_health=sections["financial_health"],
        )

    def _build_sections(self, ctx: FinancialContext) -> dict:
        """Build all dashboard sections from the financial context."""
        m = ctx.metrics  # FinancialMetricsResult from Financial Engine

        period = PeriodInfo(
            start_date=ctx.period_start,
            end_date=ctx.period_end,
            period_days=(ctx.period_end - ctx.period_start).days + 1,
        )

        user = UserContextInfo(
            user_id=ctx.user_id,
            display_name=ctx.profile.display_name,
            persona=ctx.profile.persona,
            currency=ctx.profile.currency,
            country=ctx.profile.country,
            risk_profile=ctx.profile.risk_profile,
        )

        cash_flow = self._build_cash_flow(m)
        net_worth = self._build_net_worth(m)
        investments = self._build_investments(m)
        loans = self._build_loans(ctx)
        debt = self._build_debt(m)
        goals = self._build_goals(ctx)
        budgets = self._build_budgets(m)
        financial_health = self._build_financial_health(m, ctx)

        # Top-level summary snapshot
        summary = FinancialSummarySnapshot(
            total_income=m.cash_flow.total_income if m.cash_flow else Decimal("0"),
            total_expenses=m.cash_flow.total_expenses if m.cash_flow else Decimal("0"),
            savings=m.savings.savings if m.savings else Decimal("0"),
            net_worth=m.net_worth.net_worth if m.net_worth else Decimal("0"),
            total_assets=m.net_worth.total_assets if m.net_worth else Decimal("0"),
            total_liabilities=m.net_worth.total_liabilities if m.net_worth else Decimal("0"),
            total_invested=m.portfolio_summary.total_invested if m.portfolio_summary else Decimal("0"),
            total_debt=debt.total_debt,
        )

        return {
            "period": period,
            "user": user,
            "summary": summary,
            "cash_flow": cash_flow,
            "net_worth": net_worth,
            "investments": investments,
            "loans": loans,
            "debt": debt,
            "goals": goals,
            "budgets": budgets,
            "financial_health": financial_health,
        }

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_cash_flow(m) -> CashFlowSummary:
        if m.cash_flow is None:
            return CashFlowSummary(
                total_income=Decimal("0"),
                total_expenses=Decimal("0"),
                net_cash_flow=Decimal("0"),
                savings=Decimal("0"),
                savings_rate_percent=None,
                has_data=False,
            )
        cf = m.cash_flow
        sav = m.savings
        return CashFlowSummary(
            total_income=cf.total_income,
            total_expenses=cf.total_expenses,
            net_cash_flow=cf.net_cash_flow,
            savings=sav.savings if sav else cf.net_cash_flow,
            savings_rate_percent=sav.savings_rate_percent if sav else None,
            income_by_category={k: v for k, v in cf.income_by_category.items()},
            expense_by_category={k: v for k, v in cf.expense_by_category.items()},
            has_data=True,
        )

    @staticmethod
    def _build_net_worth(m) -> NetWorthSummary:
        if m.net_worth is None:
            return NetWorthSummary(
                total_assets=Decimal("0"),
                total_liabilities=Decimal("0"),
                net_worth=Decimal("0"),
                liquid_assets=Decimal("0"),
                has_data=False,
            )
        nw = m.net_worth
        return NetWorthSummary(
            total_assets=nw.total_assets,
            total_liabilities=nw.total_liabilities,
            net_worth=nw.net_worth,
            liquid_assets=nw.liquid_assets,
            assets_by_type={k: v for k, v in nw.assets_by_type.items()},
            liabilities_by_type={k: v for k, v in nw.liabilities_by_type.items()},
            has_data=True,
        )

    @staticmethod
    def _build_investments(m) -> InvestmentSummary:
        if m.portfolio_summary is None:
            return InvestmentSummary(
                total_invested=Decimal("0"),
                current_value=Decimal("0"),
                total_gain_loss=Decimal("0"),
                total_return_percentage=Decimal("0"),
                investment_count=0,
                has_data=False,
            )
        p = m.portfolio_summary
        return InvestmentSummary(
            total_invested=p.total_invested,
            current_value=p.current_value,
            total_gain_loss=p.total_gain_loss,
            total_return_percentage=p.total_return_percentage,
            allocation_by_type={k: v for k, v in p.allocation_by_type.items()},
            allocation_percentages={k: v for k, v in p.allocation_percentages.items()},
            investment_count=len(p.allocation_by_type),
            has_data=True,
        )

    @staticmethod
    def _build_loans(ctx: FinancialContext) -> LoanSummary:
        loans = ctx.loans
        if not loans:
            return LoanSummary(
                total_outstanding=Decimal("0"),
                total_principal=Decimal("0"),
                total_monthly_emi=Decimal("0"),
                loan_count=0,
                active_loan_count=0,
                has_data=False,
            )

        active = [l for l in loans if l.status == LoanStatus.ACTIVE]
        total_outstanding = sum((l.outstanding_amount for l in loans), Decimal("0"))
        total_principal = sum((l.principal_amount for l in loans), Decimal("0"))
        total_emi = sum((l.emi or Decimal("0") for l in active), Decimal("0"))

        loan_items = [
            LoanContextItem(
                id=l.id,
                loan_type=l.loan_type,
                lender=l.lender,
                principal_amount=l.principal_amount,
                outstanding_amount=l.outstanding_amount,
                emi=l.emi,
                # interest_rate stored as fraction (0.0875) → percentage (8.75)
                interest_rate_percent=l.interest_rate * Decimal("100"),
                status=l.status,
            )
            for l in loans
        ]

        return LoanSummary(
            total_outstanding=total_outstanding,
            total_principal=total_principal,
            total_monthly_emi=total_emi,
            loan_count=len(loans),
            active_loan_count=len(active),
            loans=loan_items,
            has_data=True,
        )

    @staticmethod
    def _build_debt(m) -> DebtSummary:
        if m.debt is None:
            return DebtSummary(
                total_debt=Decimal("0"),
                monthly_obligations=Decimal("0"),
                dti_percent=None,
                has_data=False,
            )
        d = m.debt
        return DebtSummary(
            total_debt=d.total_liabilities_balance,
            monthly_obligations=d.total_monthly_emi,
            dti_percent=d.dti_percent,  # None when income is zero
            has_data=True,
        )

    @staticmethod
    def _build_goals(ctx: FinancialContext) -> GoalSummary:
        if not ctx.all_goals:
            return GoalSummary(
                total_goals=0,
                active_count=0,
                completed_count=0,
                has_data=False,
            )

        goal_items = []
        for goal, analysis in ctx.goal_analyses:
            if analysis is not None:
                item = GoalContextItem(
                    id=goal.id,
                    name=goal.name,
                    target_amount=goal.target_amount,
                    current_amount=goal.current_amount,
                    remaining_amount=analysis.remaining_amount,
                    completion_percentage=analysis.completion_percentage,
                    target_date=goal.target_date,
                    status=goal.status,
                    required_monthly_contribution=analysis.required_monthly_contribution,
                )
            else:
                # No target_date or analysis failed — basic progress without projection
                remaining = max(Decimal("0"), goal.target_amount - goal.current_amount)
                if goal.target_amount > Decimal("0"):
                    from decimal import ROUND_HALF_UP
                    pct = min(
                        Decimal("100"),
                        (goal.current_amount / goal.target_amount * Decimal("100")).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        ),
                    )
                else:
                    pct = Decimal("0")
                item = GoalContextItem(
                    id=goal.id,
                    name=goal.name,
                    target_amount=goal.target_amount,
                    current_amount=goal.current_amount,
                    remaining_amount=remaining,
                    completion_percentage=pct,
                    target_date=goal.target_date,
                    status=goal.status,
                    required_monthly_contribution=None,
                )
            goal_items.append(item)

        active_count = sum(1 for g in ctx.all_goals if g.status == GoalStatus.ACTIVE)
        completed_count = sum(1 for g in ctx.all_goals if g.status == GoalStatus.COMPLETED)

        return GoalSummary(
            total_goals=len(ctx.all_goals),
            active_count=active_count,
            completed_count=completed_count,
            goals=goal_items,
            has_data=True,
        )

    @staticmethod
    def _build_budgets(m) -> BudgetSummary:
        if m.budget_summary is None:
            return BudgetSummary(
                total_budget=Decimal("0"),
                total_spending=Decimal("0"),
                remaining_budget=Decimal("0"),
                overall_utilization_percent=Decimal("0"),
                has_data=False,
            )
        b = m.budget_summary
        return BudgetSummary(
            total_budget=b.total_budget,
            total_spending=b.total_spending,
            remaining_budget=b.total_remaining,
            overall_utilization_percent=b.overall_utilization_percentage,
            over_budget_categories=list(b.over_budget_categories),
            has_data=True,
        )

    @staticmethod
    def _build_financial_health(m, ctx: FinancialContext) -> FinancialHealthSummary:
        # Savings rate
        savings_rate = m.savings.savings_rate_percent if m.savings else None

        # DTI
        dti = m.debt.dti_percent if m.debt else None

        # Emergency fund coverage
        ef_months = m.emergency_fund_coverage_months

        # Budget utilization
        budget_util = (
            m.budget_summary.overall_utilization_percentage
            if m.budget_summary else None
        )

        # Goal completion rate
        all_goals = ctx.all_goals
        goal_completion_rate: Optional[Decimal] = None
        if all_goals:
            completed = sum(1 for g in all_goals if g.status == GoalStatus.COMPLETED)
            from decimal import ROUND_HALF_UP
            goal_completion_rate = (
                Decimal(completed) / Decimal(len(all_goals)) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Net worth
        net_worth = m.net_worth.net_worth if m.net_worth else None

        # Cash flow sign
        cash_flow_positive: Optional[bool] = None
        if m.cash_flow is not None:
            cash_flow_positive = m.cash_flow.net_cash_flow > Decimal("0")

        return FinancialHealthSummary(
            savings_rate_percent=savings_rate,
            dti_percent=dti,
            emergency_fund_months=ef_months,
            budget_utilization_percent=budget_util,
            goal_completion_rate_percent=goal_completion_rate,
            net_worth=net_worth,
            cash_flow_positive=cash_flow_positive,
        )
