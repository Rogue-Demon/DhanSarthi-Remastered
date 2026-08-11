"""
Financial Context Service for DhanSarthi — Phase 8.

Builds a complete, structured, user-scoped financial context in a single pass.
Every financial calculation is delegated to the existing Financial Engine.
No calculations are duplicated here.

Call chain:
    FinancialContextService.build_context(user_id, date_from, date_to)
        ├── repositories  (each called once — no N+1)
        ├── ProfileService.get_or_create_profile
        └── Financial Engine (calculate_financial_metrics, analyze_goal, …)

The returned ``FinancialContext`` dataclass is the upstream data source for:
  - DashboardService  → GET /api/v1/dashboard
  - GET /api/v1/financial/context
  - Future AIAdvisorService (direct service call, no HTTP hop)

Security invariant: this service accepts ``user_id`` as a parameter that
MUST originate from a verified JWT token.  It never accepts a user_id from
a client-supplied request body or query string.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

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
    NetWorthInput,
    NetWorthResult,
    PortfolioInput,
    PortfolioSummaryResult,
    SavingsResult,
    analyze_goal,
    calculate_financial_metrics,
    calculate_savings,
)
from app.models.enums import AssetType, GoalStatus, LoanStatus
from app.models.goal import Goal
from app.models.loan import Loan
from app.models.profile import Profile
from app.repositories.asset_repository import AssetRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.income_repository import IncomeRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.liability_repository import LiabilityRepository
from app.repositories.loan_repository import LoanRepository
from app.services.profile_service import ProfileService

# Default rolling window when the caller supplies no explicit period.
_DEFAULT_PERIOD_DAYS = 30


# ---------------------------------------------------------------------------
# Internal data container
# ---------------------------------------------------------------------------


@dataclass
class FinancialContext:
    """
    Structured, user-scoped financial context.

    This is a pure Python dataclass (not an ORM model, not a Pydantic schema).
    It is the canonical representation consumed by DashboardService and the
    future AI Advisor.

    Fields marked ``Optional[…]`` are ``None`` when no underlying data exists.
    This preserves the semantic distinction between zero and "no data".
    """

    # Identity
    user_id: int
    profile: Profile

    # Period used for all flow calculations
    period_start: date
    period_end: date

    # Financial Engine results (None = no data for that dimension)
    metrics: FinancialMetricsResult

    # Per-goal analysis (only for goals with a target_date)
    goal_analyses: List[tuple[Goal, Optional[GoalAnalysisResult]]] = field(
        default_factory=list
    )
    all_goals: List[Goal] = field(default_factory=list)

    # Raw loan records (for per-loan detail in LoanSummary)
    loans: List[Loan] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class FinancialContextService:
    """
    Builds a complete financial context for a single authenticated user.

    Responsibility:
      - Load all required data from repositories (one query per domain).
      - Translate ORM objects → Financial Engine input types.
      - Delegate all calculations to the Financial Engine.
      - Return a ``FinancialContext`` dataclass.

    This service holds no per-instance state beyond the db session.
    It is safe to call multiple times within a request for different users
    (provided a fresh instance is used — which FastAPI dependency injection
    guarantees).
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._profile_svc = ProfileService(db)
        self._income_repo = IncomeRepository(db)
        self._expense_repo = ExpenseRepository(db)
        self._asset_repo = AssetRepository(db)
        self._liability_repo = LiabilityRepository(db)
        self._investment_repo = InvestmentRepository(db)
        self._loan_repo = LoanRepository(db)
        self._goal_repo = GoalRepository(db)
        self._budget_repo = BudgetRepository(db)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build_context(
        self,
        user_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> FinancialContext:
        """
        Build and return a complete FinancialContext for the given user.

        Args:
            user_id: Authenticated user's ID (from verified JWT).
            date_from: Start of the calculation period (inclusive).
            date_to: End of the calculation period (inclusive).

        Returns:
            FinancialContext: Fully populated context object.
        """
        # Resolve and clamp the calculation period.
        period_end = date_to or date.today()
        period_start = date_from or (period_end - timedelta(days=_DEFAULT_PERIOD_DAYS - 1))

        # 1. Profile — auto-provision if missing.
        profile = self._profile_svc.get_or_create_profile(user_id)

        # 2. Load all financial data (one repository call per domain).
        incomes = self._income_repo.list_for_user(
            user_id, date_from=period_start, date_to=period_end, limit=1000
        )
        expenses = self._expense_repo.list_for_user(
            user_id, date_from=period_start, date_to=period_end, limit=1000
        )
        assets = self._asset_repo.list_for_user(user_id)
        liabilities = self._liability_repo.list_for_user(user_id)
        investments = self._investment_repo.list_for_user(user_id)
        loans = self._loan_repo.list_for_user(user_id)
        goals = self._goal_repo.list_for_user(user_id)
        budgets = self._budget_repo.list_for_user(user_id)

        # 3. Translate ORM objects → Financial Engine input types.
        income_inputs = [
            IncomeItemInput(
                amount=inc.amount,
                category=inc.category,
                frequency=inc.frequency,
                source=inc.source,
                is_recurring=getattr(inc.frequency, "name", "ONE_TIME") != "ONE_TIME",
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

        asset_inputs = [
            AssetItemInput(
                name=a.name,
                asset_type=a.asset_type,
                current_value=a.value,
                is_liquid=a.asset_type in (AssetType.CASH, AssetType.BANK_BALANCE),
            )
            for a in assets
        ]

        liability_inputs = [
            LiabilityItemInput(
                name=li.name,
                liability_type=li.liability_type,
                outstanding_balance=li.outstanding_amount,
                monthly_payment=Decimal("0"),
            )
            for li in liabilities
        ]

        investment_inputs = [
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

        # Build monthly essential expenses for emergency fund calculation.
        monthly_essential = sum(
            (exp.amount for exp in expenses if getattr(exp, "is_essential", False)),
            Decimal("0"),
        )

        # Aggregate expense spending per category for budget matching.
        spending_map: dict[str, Decimal] = {}
        for exp in expenses:
            cat = exp.category
            spending_map[cat] = spending_map.get(cat, Decimal("0")) + exp.amount

        budget_inputs: List[BudgetCategoryInput] = []
        for b in budgets:
            actual = spending_map.get(b.category, Decimal("0"))
            budget_inputs.append(
                BudgetCategoryInput(
                    category=b.category,
                    budget_amount=b.amount,
                    actual_spending=actual,
                )
            )

        # 4. Build Financial Engine input payloads.
        cf_input = CashFlowInput(
            incomes=income_inputs,
            expenses=expense_inputs,
            reference_date=period_end,
        ) if income_inputs or expense_inputs else None

        nw_input = NetWorthInput(
            assets=asset_inputs,
            liabilities=liability_inputs,
            reference_date=period_end,
        ) if asset_inputs or liability_inputs else None

        port_input = PortfolioInput(
            investments=investment_inputs,
            reference_date=period_end,
        ) if investment_inputs else None

        budget_input = BudgetAnalysisInput(
            category_budgets=budget_inputs,
        ) if budget_inputs else None

        metrics_input = FinancialMetricsInput(
            cash_flow_input=cf_input,
            net_worth_input=nw_input,
            portfolio_input=port_input,
            budget_input=budget_input,
            monthly_essential_expenses=monthly_essential if monthly_essential > Decimal("0") else None,
            reference_date=period_end,
        )

        # 5. Single Financial Engine call — computes all sub-metrics at once.
        metrics = calculate_financial_metrics(metrics_input)

        # 6. Per-goal analysis (only goals that have a target_date).
        goal_analyses: List[tuple[Goal, Optional[GoalAnalysisResult]]] = []
        for goal in goals:
            if goal.target_date is not None:
                try:
                    goal_input = GoalInput(
                        title=goal.name,  # Goal model uses `name`; GoalInput uses `title`
                        target_amount=goal.target_amount,
                        current_amount=goal.current_amount,
                        target_date=goal.target_date,
                        reference_date=period_end,
                    )
                    analysis = analyze_goal(goal_input)
                    goal_analyses.append((goal, analysis))
                except Exception:
                    # If a goal has bad data, skip its analysis but keep the goal.
                    goal_analyses.append((goal, None))
            else:
                # No target date — we can report basic progress without analysis.
                goal_analyses.append((goal, None))

        return FinancialContext(
            user_id=user_id,
            profile=profile,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            goal_analyses=goal_analyses,
            all_goals=goals,
            loans=loans,
        )
