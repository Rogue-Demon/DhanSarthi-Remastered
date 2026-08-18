"""
Financial Intelligence and Decision Engine Service.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.services.financial_context_service import FinancialContextService
from app.financial_intelligence.schemas import (
    FinancialInsight,
    FinancialIntelligenceSummary,
    LoanScenarioResult,
    GenericScenarioResult,
)
from app.financial_intelligence.analyzers.cash_flow import analyze_cash_flow, analyze_savings
from app.financial_intelligence.analyzers.expenses import analyze_expenses
from app.financial_intelligence.analyzers.budget import analyze_budget
from app.financial_intelligence.analyzers.debt import analyze_debt_burden
from app.financial_intelligence.analyzers.emergency_fund import analyze_emergency_fund
from app.financial_intelligence.analyzers.investments import analyze_investments
from app.financial_intelligence.analyzers.goals import analyze_goals
from app.financial_intelligence.scenarios.engine import (
    run_loan_scenario as sim_loan_scenario,
    run_savings_scenario as sim_savings_scenario,
    run_investment_scenario as sim_investment_scenario,
    run_goal_scenario as sim_goal_scenario,
)
from app.financial_intelligence.rules.engine import evaluate_warnings, evaluate_opportunities
from app.repositories.goal_repository import GoalRepository
from app.repositories.expense_repository import ExpenseRepository
from app.core.exceptions import ResourceNotFoundError
from app.financial_intelligence.exceptions import FinancialIntelligenceAccessDeniedError


class FinancialIntelligenceService:
    """
    Orchestrates deterministic financial analysis, rules, and scenarios.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._dash_svc = DashboardService(db)
        self._context_svc = FinancialContextService(db)
        self._goal_repo = GoalRepository(db)
        self._expense_repo = ExpenseRepository(db)

    def build_summary(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> FinancialIntelligenceSummary:
        """
        Build a consolidated financial health summary for the authenticated user.
        """
        # 1. Retrieve the authenticated user's baseline dashboard
        dash = self._dash_svc.build_dashboard(user_id=user_id, date_from=date_from, date_to=date_to)
        context = self._context_svc.build_context(user_id=user_id, date_from=date_from, date_to=date_to)
        
        # Load user's transaction records to analyze category std deviation anomalies
        all_expenses = self._expense_repo.list_for_user(user_id, limit=500)

        # 2. Execute Analyzers
        period_days = (dash.period.end_date - dash.period.start_date).days + 1
        
        # Calculate cash flow trend history MoM
        history_flows = [dash.cash_flow.net_cash_flow]
        
        cash_flow_insight = analyze_cash_flow(dash.cash_flow, period_days, history_flows)
        savings_insight = analyze_savings(dash.cash_flow, period_days)
        expenses_insight = analyze_expenses(dash.cash_flow, period_days, all_expenses)
        budget_insight = analyze_budget(dash.budgets)
        debt_insight = analyze_debt_burden(dash.debt)
        
        essential_expenses = Decimal("0")
        if context.metrics and context.metrics.cash_flow:
            for exp in context.metrics.cash_flow.expense_by_category.keys():
                # check if essential
                if exp.lower() in ["housing", "rent", "food", "groceries", "utilities", "healthcare", "medical", "transport", "transportation", "education", "debt payments", "emi"]:
                    essential_expenses += context.metrics.cash_flow.expense_by_category[exp]
        
        # emergency fund
        emergency_fund_insight = analyze_emergency_fund(dash.financial_health, dash.net_worth, essential_expenses)
        investments_insight = analyze_investments(dash.investments)
        goals_insights = analyze_goals(dash.goals)

        # Copy calculated metrics back to dashboard model for rule triggers
        if dash.financial_health:
            if debt_insight.status != "INSUFFICIENT_DATA":
                dash.financial_health.dti_percent = debt_insight.value
            if emergency_fund_insight.status != "INSUFFICIENT_DATA":
                dash.financial_health.emergency_fund_months = emergency_fund_insight.value

        # 3. Rules Engine & Financial Health Model
        warnings = evaluate_warnings(dash)
        opportunities = evaluate_opportunities(dash)

        health_snapshot = None
        signals = []
        if context.metrics:
            try:
                from app.financial.health_snapshot import build_financial_health_snapshot
                from app.financial.signals import evaluate_financial_signals

                health_snapshot = build_financial_health_snapshot(
                    user_id=user_id,
                    metrics=context.metrics,
                    reference_date=dash.period.end_date,
                )
                signals = evaluate_financial_signals(snapshot=health_snapshot)
            except Exception:
                pass

        # 4. Resolve Data Quality
        has_income = dash.cash_flow.has_data and dash.cash_flow.total_income > 0
        has_expenses = dash.cash_flow.has_data and dash.cash_flow.total_expenses > 0
        has_assets = dash.net_worth.has_data and dash.net_worth.total_assets > 0
        has_liabilities = dash.net_worth.has_data and dash.net_worth.total_liabilities > 0
        has_budget = dash.budgets.has_data

        if has_income and has_expenses and has_assets and has_liabilities and has_budget:
            data_quality = "COMPLETE"
        elif has_income and has_expenses and has_assets and has_liabilities:
            data_quality = "GOOD"
        elif has_income and has_expenses:
            data_quality = "PARTIAL"
        else:
            data_quality = "LIMITED"

        return FinancialIntelligenceSummary(
            cash_flow=cash_flow_insight,
            savings=savings_insight,
            expenses=expenses_insight,
            budget=budget_insight,
            debt=debt_insight,
            emergency_fund=emergency_fund_insight,
            investments=investments_insight,
            goals=goals_insights,
            warnings=warnings,
            opportunities=opportunities,
            health_snapshot=health_snapshot,
            signals=signals,
            data_quality=data_quality,
            data_as_of=datetime.now().isoformat(),
        )

    def run_loan_scenario(
        self,
        user_id: int,
        principal: Decimal,
        annual_interest_rate_percent: Decimal,
        tenure_months: int,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> LoanScenarioResult:
        """
        Evaluate loan affordability based on proposed terms and user baseline context.
        """
        dash = self._dash_svc.build_dashboard(user_id=user_id, date_from=date_from, date_to=date_to)
        
        monthly_income = dash.summary.total_income
        existing_debt = dash.debt.monthly_obligations
        
        # Calculate essential expenses
        context = self._context_svc.build_context(user_id=user_id, date_from=date_from, date_to=date_to)
        essential_expenses = Decimal("0")
        if context.metrics and context.metrics.cash_flow:
            for exp in context.metrics.cash_flow.expense_by_category.keys():
                if exp.lower() in ["housing", "rent", "food", "groceries", "utilities", "healthcare", "medical", "transport", "transportation", "education", "debt payments", "emi"]:
                    essential_expenses += context.metrics.cash_flow.expense_by_category[exp]
        if essential_expenses == Decimal("0"):
            essential_expenses = dash.summary.total_expenses

        return sim_loan_scenario(
            principal=principal,
            annual_interest_rate_percent=annual_interest_rate_percent,
            tenure_months=tenure_months,
            monthly_income=monthly_income,
            existing_monthly_debt=existing_debt,
            essential_expenses=essential_expenses,
        )

    def run_savings_scenario(
        self,
        user_id: int,
        expense_reduction: Decimal,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> GenericScenarioResult:
        """
        Simulate impact of target expense reduction on user's monthly surplus.
        """
        dash = self._dash_svc.build_dashboard(user_id=user_id, date_from=date_from, date_to=date_to)
        base_income = dash.summary.total_income
        base_expenses = dash.summary.total_expenses

        return sim_savings_scenario(
            base_expenses=base_expenses,
            expense_reduction=expense_reduction,
            base_income=base_income,
        )

    def run_investment_scenario(
        self,
        user_id: int,
        monthly_contribution: Decimal,
        expected_annual_return_percent: Decimal,
        duration_years: Decimal,
    ) -> GenericScenarioResult:
        """
        Simulate standard Systematic Investment Plan (SIP) growth.
        """
        return sim_investment_scenario(
            monthly_contribution=monthly_contribution,
            expected_annual_return_percent=expected_annual_return_percent,
            duration_years=duration_years,
        )

    def run_goal_scenario(
        self,
        user_id: int,
        goal_id: int,
        proposed_monthly_contribution: Decimal,
    ) -> GenericScenarioResult:
        """
        Simulate goal feasibility and shortfall adjustments for a user-owned goal.
        """
        goal = self._goal_repo.get_by_id(goal_id)
        if not goal:
            raise ResourceNotFoundError(f"Goal with ID {goal_id} not found.")
            
        if goal.user_id != user_id:
            raise FinancialIntelligenceAccessDeniedError("You are not authorized to access this goal.")

        target = goal.target_amount
        current = goal.current_amount
        
        # Calculate months remaining based on target date
        today = date.today()
        if goal.target_date and goal.target_date > today:
            months = (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month)
            if months <= 0:
                months = 1
        else:
            months = 12  # Default to 1 year projection if no date

        return sim_goal_scenario(
            target_amount=target,
            current_amount=current,
            months_remaining=months,
            proposed_monthly_contribution=proposed_monthly_contribution,
        )
