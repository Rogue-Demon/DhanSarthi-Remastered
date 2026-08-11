"""
Financial Service for DhanSarthi.

Acts as the bridge between PostgreSQL database repositories and the pure,
deterministic Financial Engine.  Translates ORM models into Financial Engine input
types and invokes financial engine calculations.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.enums import AssetType

from app.financial import (
    AssetItemInput,
    BudgetAnalysisInput,
    BudgetAnalysisResult,
    BudgetCategoryInput,
    CashFlowInput,
    CashFlowResult,
    DebtAnalysisResult,
    ExpenseItemInput,
    FinancialMetricsInput,
    FinancialMetricsResult,
    GoalAnalysisResult,
    GoalInput,
    IncomeItemInput,
    InvestmentItemInput,
    LiabilityItemInput,
    LoanAffordabilityInput,
    LoanAffordabilityResult,
    LoanCalculationResult,
    LoanInput,
    NetWorthInput,
    NetWorthResult,
    PortfolioInput,
    PortfolioSummaryResult,
    SIPCalculationResult,
    SIPInput,
    SavingsResult,
    analyze_budget,
    analyze_debt,
    analyze_goal,
    analyze_loan_affordability,
    analyze_portfolio,
    calculate_cash_flow,
    calculate_financial_metrics,
    calculate_loan,
    calculate_net_worth,
    calculate_savings,
    calculate_sip,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.income_repository import IncomeRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.liability_repository import LiabilityRepository
from app.repositories.loan_repository import LoanRepository


class FinancialService:
    """Coordinates data retrieval from DB repositories and passes typed data to Financial Engine."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._income_repo = IncomeRepository(db)
        self._expense_repo = ExpenseRepository(db)
        self._asset_repo = AssetRepository(db)
        self._liability_repo = LiabilityRepository(db)
        self._investment_repo = InvestmentRepository(db)
        self._loan_repo = LoanRepository(db)
        self._goal_repo = GoalRepository(db)
        self._budget_repo = BudgetRepository(db)

    # ------------------------------------------------------------------
    # Cash Flow & Savings
    # ------------------------------------------------------------------

    def get_user_cash_flow(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
        reference_date: date | None = None,
    ) -> CashFlowResult:
        """Fetch user incomes and expenses from DB and calculate cash flow."""
        incomes = self._income_repo.list_for_user(user_id, date_from=date_from, date_to=date_to)
        expenses = self._expense_repo.list_for_user(user_id, date_from=date_from, date_to=date_to)

        income_inputs = [
            IncomeItemInput(
                amount=inc.amount,
                category=inc.category,
                frequency=inc.frequency,
                source=inc.source,
                is_recurring=inc.frequency.name != "ONE_TIME" if hasattr(inc.frequency, "name") else True,
            )
            for inc in incomes
        ]

        expense_inputs = [
            ExpenseItemInput(
                amount=exp.amount,
                category=exp.category,
                frequency=exp.frequency or "MONTHLY",
                is_essential=getattr(exp, "is_essential", False),
                source=exp.description,
            )
            for exp in expenses
        ]

        payload = CashFlowInput(
            incomes=income_inputs,
            expenses=expense_inputs,
            reference_date=reference_date,
        )
        return calculate_cash_flow(payload)

    def get_user_savings(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
        reference_date: date | None = None,
    ) -> SavingsResult:
        """Fetch user cash flow and calculate savings rate."""
        cf = self.get_user_cash_flow(user_id, date_from=date_from, date_to=date_to, reference_date=reference_date)
        return calculate_savings(cf.total_income, cf.total_expenses, reference_date=reference_date)

    # ------------------------------------------------------------------
    # Net Worth & Debt
    # ------------------------------------------------------------------

    def get_user_net_worth(self, user_id: int, reference_date: date | None = None) -> NetWorthResult:
        """Fetch user assets and liabilities from DB and calculate net worth."""
        assets = self._asset_repo.list_for_user(user_id)
        liabilities = self._liability_repo.list_for_user(user_id)

        asset_inputs = [
            AssetItemInput(
                name=a.name,
                asset_type=a.asset_type,
                current_value=a.value,
                is_liquid=(a.asset_type in (AssetType.CASH, AssetType.BANK_BALANCE)),
            )
            for a in assets
        ]

        liability_inputs = [
            LiabilityItemInput(
                name=l.name,
                liability_type=l.liability_type,
                outstanding_balance=l.outstanding_amount,
                monthly_payment=Decimal("0"),
            )
            for l in liabilities
        ]

        payload = NetWorthInput(
            assets=asset_inputs,
            liabilities=liability_inputs,
            reference_date=reference_date,
        )
        return calculate_net_worth(payload)

    def get_user_debt_analysis(
        self, user_id: int, reference_date: date | None = None
    ) -> DebtAnalysisResult:
        """Fetch liabilities and monthly income to compute debt metrics."""
        liabilities = self._liability_repo.list_for_user(user_id)
        cf = self.get_user_cash_flow(user_id, reference_date=reference_date)

        liability_inputs = [
            LiabilityItemInput(
                name=l.name,
                liability_type=l.liability_type,
                outstanding_balance=l.outstanding_amount,
                monthly_payment=Decimal("0"),
            )
            for l in liabilities
        ]

        return analyze_debt(
            liabilities=liability_inputs,
            gross_monthly_income=cf.total_income,
            reference_date=reference_date,
        )

    # ------------------------------------------------------------------
    # Portfolio & Investments
    # ------------------------------------------------------------------

    def get_user_portfolio_summary(
        self, user_id: int, reference_date: date | None = None
    ) -> PortfolioSummaryResult:
        """Fetch user investments from DB and compute portfolio summary."""
        investments = self._investment_repo.list_for_user(user_id)

        inv_inputs = [
            InvestmentItemInput(
                name=inv.name,
                investment_type=inv.investment_type,
                invested_amount=inv.principal,
                current_value=inv.current_value,
                purchase_date=inv.purchase_date,
                units=inv.quantity,
            )
            for inv in investments
        ]

        payload = PortfolioInput(investments=inv_inputs, reference_date=reference_date)
        return analyze_portfolio(payload)

    # ------------------------------------------------------------------
    # Goals & Budgets
    # ------------------------------------------------------------------

    def get_user_goal_analysis(self, goal_id: int, user_id: int) -> GoalAnalysisResult:
        """Fetch a specific user goal and compute progress and required contribution."""
        goal = self._goal_repo.get_by_id_for_user(goal_id, user_id)
        if goal is None:
            from app.core.exceptions import ResourceNotFoundError

            raise ResourceNotFoundError(resource="Goal", identifier=goal_id)

        payload = GoalInput(
            title=goal.title,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
        )
        return analyze_goal(payload)

    def get_user_budget_analysis(self, user_id: int) -> BudgetAnalysisResult:
        """Fetch active budgets for user and match with actual category spending."""
        budgets = self._budget_repo.list_for_user(user_id)
        expenses = self._expense_repo.list_for_user(user_id)

        # Aggregate actual spending by category
        spending_map: dict[str, Decimal] = {}
        for exp in expenses:
            cat = exp.category
            spending_map[cat] = spending_map.get(cat, Decimal("0")) + exp.amount

        cat_inputs: List[BudgetCategoryInput] = []
        for b in budgets:
            actual = spending_map.get(b.category, Decimal("0"))
            cat_inputs.append(
                BudgetCategoryInput(
                    category=b.category,
                    budget_amount=b.amount,
                    actual_spending=actual,
                )
            )

        payload = BudgetAnalysisInput(category_budgets=cat_inputs)
        return analyze_budget(payload)

    # ------------------------------------------------------------------
    # Consolidated Metrics
    # ------------------------------------------------------------------

    def get_user_financial_metrics(
        self, user_id: int, reference_date: date | None = None
    ) -> FinancialMetricsResult:
        """Aggregate all user financial dimensions into structured metrics."""
        cf_input = CashFlowInput(
            incomes=[
                IncomeItemInput(
                    amount=inc.amount,
                    category=inc.category,
                    frequency=inc.frequency,
                )
                for inc in self._income_repo.list_for_user(user_id)
            ],
            expenses=[
                ExpenseItemInput(
                    amount=exp.amount,
                    category=exp.category,
                    frequency=exp.frequency or "MONTHLY",
                    is_essential=getattr(exp, "is_essential", False),
                )
                for exp in self._expense_repo.list_for_user(user_id)
            ],
            reference_date=reference_date,
        )

        nw_input = NetWorthInput(
            assets=[
                AssetItemInput(
                    name=a.name,
                    asset_type=a.asset_type,
                    current_value=a.value,
                    is_liquid=(a.asset_type in (AssetType.CASH, AssetType.BANK_BALANCE)),
                )
                for a in self._asset_repo.list_for_user(user_id)
            ],
            liabilities=[
                LiabilityItemInput(
                    name=l.name,
                    liability_type=l.liability_type,
                    outstanding_balance=l.outstanding_amount,
                    monthly_payment=Decimal("0"),
                )
                for l in self._liability_repo.list_for_user(user_id)
            ],
            reference_date=reference_date,
        )

        port_input = PortfolioInput(
            investments=[
                InvestmentItemInput(
                    name=inv.name,
                    investment_type=inv.investment_type,
                    invested_amount=inv.principal,
                    current_value=inv.current_value,
                )
                for inv in self._investment_repo.list_for_user(user_id)
            ]
        )

        payload = FinancialMetricsInput(
            cash_flow_input=cf_input,
            net_worth_input=nw_input,
            portfolio_input=port_input,
            reference_date=reference_date,
        )
        return calculate_financial_metrics(payload)

    # ------------------------------------------------------------------
    # Pure Calculations Delegated directly to Financial Engine
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_loan(input_data: LoanInput) -> LoanCalculationResult:
        """Delegate pure loan EMI calculation."""
        return calculate_loan(input_data)

    @staticmethod
    def calculate_sip(input_data: SIPInput) -> SIPCalculationResult:
        """Delegate pure SIP projection calculation."""
        return calculate_sip(input_data)

    @staticmethod
    def analyze_loan_affordability(input_data: LoanAffordabilityInput) -> LoanAffordabilityResult:
        """Delegate pure loan affordability analysis."""
        return analyze_loan_affordability(input_data)
