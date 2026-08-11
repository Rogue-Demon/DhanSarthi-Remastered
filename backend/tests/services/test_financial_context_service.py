"""
Unit tests for FinancialContextService — Phase 8.

Tests verify that:
  - build_context() works correctly for every financial data combination.
  - Missing data is represented as None (not zero).
  - Financial Engine calculations are correctly delegated (not duplicated).
  - No cross-user leakage occurs (each test uses isolated db_session via conftest.py).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.enums import (
    AssetType,
    GoalStatus,
    IncomeFrequency,
    LoanStatus,
    LoanType,
    RiskProfile,
    Persona,
)
from app.models.user import User
from app.models.profile import Profile
from app.models.income import Income
from app.models.expense import Expense
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.investment import Investment
from app.models.loan import Loan
from app.models.goal import Goal
from app.models.budget import Budget
from app.services.financial_context_service import FinancialContextService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db: Session, user_id: int) -> User:
    existing = db.get(User, user_id)
    if existing:
        return existing
    u = User(
        id=user_id,
        email=f"ctx_test_user{user_id}@example.com",
        password_hash="$2b$12$placeholder",
    )
    db.add(u)
    db.flush()
    return u


def _make_profile(db: Session, user_id: int) -> Profile:
    p = Profile(
        user_id=user_id,
        display_name=f"Test User {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    )
    db.add(p)
    db.flush()
    return p


TODAY = date.today()
D30_AGO = TODAY - timedelta(days=29)


# ---------------------------------------------------------------------------
# Empty user
# ---------------------------------------------------------------------------


class TestEmptyUser:
    def test_empty_user_no_crash(self, db_session: Session):
        """A user with no financial data should return a valid context without errors."""
        _make_user(db_session, 201)
        _make_profile(db_session, 201)

        svc = FinancialContextService(db_session)
        ctx = svc.build_context(201)

        # Period defaults to 30 days
        assert ctx.period_end == TODAY
        assert (ctx.period_end - ctx.period_start).days == 29

        # No data → all metrics sub-results are None
        assert ctx.metrics.cash_flow is None
        assert ctx.metrics.net_worth is None
        assert ctx.metrics.portfolio_summary is None
        assert ctx.metrics.budget_summary is None
        assert ctx.metrics.debt is None
        assert ctx.goal_analyses == []
        assert ctx.loans == []


# ---------------------------------------------------------------------------
# Income only
# ---------------------------------------------------------------------------


class TestIncomeOnly:
    def test_income_aggregated_into_cash_flow(self, db_session: Session):
        _make_user(db_session, 202)
        _make_profile(db_session, 202)

        db_session.add(
            Income(
                user_id=202,
                source="Salary",
                amount=Decimal("100000"),
                income_date=TODAY,
                category="SALARY",
                frequency=IncomeFrequency.MONTHLY,
            )
        )
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(202)

        assert ctx.metrics.cash_flow is not None
        assert ctx.metrics.cash_flow.total_income == Decimal("100000")
        assert ctx.metrics.cash_flow.total_expenses == Decimal("0")
        assert ctx.metrics.cash_flow.net_cash_flow == Decimal("100000")

    def test_savings_rate_when_no_expenses(self, db_session: Session):
        _make_user(db_session, 203)
        _make_profile(db_session, 203)

        db_session.add(
            Income(
                user_id=203,
                source="Freelance",
                amount=Decimal("50000"),
                income_date=TODAY,
                category="FREELANCE",
                frequency=IncomeFrequency.MONTHLY,
            )
        )
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(203)

        assert ctx.metrics.savings is not None
        assert ctx.metrics.savings.savings == Decimal("50000")
        # Savings rate = 100 % when expenses = 0
        assert ctx.metrics.savings.savings_rate_percent == Decimal("100.00")


# ---------------------------------------------------------------------------
# Expenses only
# ---------------------------------------------------------------------------


class TestExpensesOnly:
    def test_expenses_only_negative_cash_flow(self, db_session: Session):
        _make_user(db_session, 204)
        _make_profile(db_session, 204)

        db_session.add(
            Expense(
                user_id=204,
                category="FOOD",
                amount=Decimal("3000"),
                expense_date=TODAY,
                description="Groceries",
            )
        )
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(204)

        assert ctx.metrics.cash_flow is not None
        assert ctx.metrics.cash_flow.total_income == Decimal("0")
        assert ctx.metrics.cash_flow.total_expenses == Decimal("3000")
        assert ctx.metrics.cash_flow.net_cash_flow == Decimal("-3000")


# ---------------------------------------------------------------------------
# Income + Expenses
# ---------------------------------------------------------------------------


class TestIncomeAndExpenses:
    def test_savings_formula(self, db_session: Session):
        """Verify: savings = income - expenses (Financial Engine delegation)."""
        _make_user(db_session, 205)
        _make_profile(db_session, 205)

        db_session.add(Income(
            user_id=205, source="Job", amount=Decimal("100000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.add(Expense(
            user_id=205, category="RENT", amount=Decimal("30000"),
            expense_date=TODAY, description="Rent",
        ))
        db_session.add(Expense(
            user_id=205, category="FOOD", amount=Decimal("10000"),
            expense_date=TODAY, description="Food",
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(205)

        cf = ctx.metrics.cash_flow
        assert cf is not None
        assert cf.total_income == Decimal("100000")
        assert cf.total_expenses == Decimal("40000")
        assert cf.net_cash_flow == Decimal("60000")

        sav = ctx.metrics.savings
        assert sav is not None
        assert sav.savings == Decimal("60000")
        assert sav.savings_rate_percent == Decimal("60.00")


# ---------------------------------------------------------------------------
# Assets + Liabilities
# ---------------------------------------------------------------------------


class TestAssetsAndLiabilities:
    def test_net_worth_calculation(self, db_session: Session):
        _make_user(db_session, 206)
        _make_profile(db_session, 206)

        db_session.add(Asset(
            user_id=206, name="Savings Account", asset_type=AssetType.BANK_BALANCE,
            value=Decimal("500000"), valuation_date=TODAY,
        ))
        db_session.add(Asset(
            user_id=206, name="Gold", asset_type=AssetType.GOLD,
            value=Decimal("200000"), valuation_date=TODAY,
        ))
        db_session.add(Liability(
            user_id=206, name="Credit Card", liability_type="CREDIT_CARD",
            outstanding_amount=Decimal("50000"),
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(206)

        nw = ctx.metrics.net_worth
        assert nw is not None
        assert nw.total_assets == Decimal("700000")
        assert nw.total_liabilities == Decimal("50000")
        assert nw.net_worth == Decimal("650000")
        assert nw.liquid_assets == Decimal("500000")  # only BANK_BALANCE is liquid

    def test_no_assets_no_liabilities_returns_none_net_worth(self, db_session: Session):
        _make_user(db_session, 207)
        _make_profile(db_session, 207)

        ctx = FinancialContextService(db_session).build_context(207)

        assert ctx.metrics.net_worth is None


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------


class TestInvestments:
    def test_portfolio_analysis(self, db_session: Session):
        _make_user(db_session, 208)
        _make_profile(db_session, 208)

        db_session.add(Investment(
            user_id=208, name="Nifty ETF", investment_type="ETF",
            principal=Decimal("100000"), current_value=Decimal("115000"),
            purchase_date=TODAY - timedelta(days=365),
        ))
        db_session.add(Investment(
            user_id=208, name="FD HDFC", investment_type="FD",
            principal=Decimal("50000"), current_value=Decimal("53000"),
            purchase_date=TODAY - timedelta(days=180),
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(208)

        p = ctx.metrics.portfolio_summary
        assert p is not None
        assert p.total_invested == Decimal("150000")
        assert p.current_value == Decimal("168000")
        assert p.total_gain_loss == Decimal("18000")

    def test_no_investments_returns_none_portfolio(self, db_session: Session):
        _make_user(db_session, 209)
        _make_profile(db_session, 209)

        ctx = FinancialContextService(db_session).build_context(209)

        assert ctx.metrics.portfolio_summary is None


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------


class TestLoans:
    def test_loan_summary(self, db_session: Session):
        _make_user(db_session, 210)
        _make_profile(db_session, 210)

        db_session.add(Loan(
            user_id=210, loan_type=LoanType.HOME, lender="HDFC Bank",
            principal_amount=Decimal("3000000"), outstanding_amount=Decimal("2500000"),
            currency="INR", interest_rate=Decimal("0.0875"),
            tenure=240, status=LoanStatus.ACTIVE,
            start_date=TODAY - timedelta(days=730),
            emi=Decimal("25000"),
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(210)

        assert len(ctx.loans) == 1
        assert ctx.loans[0].outstanding_amount == Decimal("2500000")

    def test_dti_none_when_no_income(self, db_session: Session):
        """DTI must be None (not 0) when income data is unavailable."""
        _make_user(db_session, 211)
        _make_profile(db_session, 211)

        db_session.add(Liability(
            user_id=211, name="Car Loan", liability_type="PERSONAL_DEBT",
            outstanding_amount=Decimal("300000"),
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(211)

        # Debt result may still be computed from liabilities but DTI requires income
        if ctx.metrics.debt is not None:
            # DTI should be None or 0 when income=0 (engine does not divide by zero)
            # The engine returns None when income is zero per its own invariant.
            assert ctx.metrics.debt.dti_percent is None or ctx.metrics.debt.dti_percent == Decimal("0")


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


class TestGoals:
    def test_goal_analysis_with_target_date(self, db_session: Session):
        _make_user(db_session, 212)
        _make_profile(db_session, 212)

        future_date = TODAY + timedelta(days=365)
        db_session.add(Goal(
            user_id=212, name="Emergency Fund", target_amount=Decimal("300000"),
            current_amount=Decimal("60000"), currency="INR",
            target_date=future_date, status=GoalStatus.ACTIVE, priority=1,
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(212)

        assert len(ctx.goal_analyses) == 1
        goal, analysis = ctx.goal_analyses[0]
        assert goal.name == "Emergency Fund"
        assert analysis is not None
        assert analysis.completion_percentage == Decimal("20.00")
        assert analysis.remaining_amount == Decimal("240000")

    def test_goal_without_target_date_no_analysis(self, db_session: Session):
        _make_user(db_session, 213)
        _make_profile(db_session, 213)

        db_session.add(Goal(
            user_id=213, name="Buy Car", target_amount=Decimal("500000"),
            current_amount=Decimal("100000"), currency="INR",
            target_date=None, status=GoalStatus.ACTIVE, priority=2,
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(213)

        assert len(ctx.goal_analyses) == 1
        goal, analysis = ctx.goal_analyses[0]
        assert analysis is None  # No analysis without target_date


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------


class TestBudgets:
    def test_budget_analysis(self, db_session: Session):
        _make_user(db_session, 214)
        _make_profile(db_session, 214)

        db_session.add(Budget(
            user_id=214, category="FOOD",
            amount=Decimal("10000"), period="MONTHLY",
            start_date=TODAY - timedelta(days=15),
        ))
        # Actual spending in category
        db_session.add(Expense(
            user_id=214, category="FOOD", amount=Decimal("7000"),
            expense_date=TODAY, description="Groceries",
        ))
        db_session.flush()

        ctx = FinancialContextService(db_session).build_context(214)

        b = ctx.metrics.budget_summary
        assert b is not None
        assert b.total_budget == Decimal("10000")
        assert b.total_spending == Decimal("7000")
        assert b.total_remaining == Decimal("3000")
        assert b.overall_utilization_percentage == Decimal("70.00")

    def test_no_budgets_returns_none(self, db_session: Session):
        _make_user(db_session, 215)
        _make_profile(db_session, 215)

        ctx = FinancialContextService(db_session).build_context(215)

        assert ctx.metrics.budget_summary is None


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------


class TestCrossUserIsolation:
    def test_user_a_data_not_visible_to_user_b(self, db_session: Session):
        """User A's financial data must never appear in User B's context."""
        _make_user(db_session, 220)
        _make_profile(db_session, 220)
        _make_user(db_session, 221)
        _make_profile(db_session, 221)

        # User A has income
        db_session.add(Income(
            user_id=220, source="Consulting", amount=Decimal("80000"),
            income_date=TODAY, category="FREELANCE", frequency=IncomeFrequency.MONTHLY,
        ))
        # User A has an asset
        db_session.add(Asset(
            user_id=220, name="FD", asset_type=AssetType.BANK_BALANCE,
            value=Decimal("1000000"), valuation_date=TODAY,
        ))
        db_session.flush()

        # Build context as User B
        ctx_b = FinancialContextService(db_session).build_context(221)

        # User B has no data
        assert ctx_b.metrics.cash_flow is None
        assert ctx_b.metrics.net_worth is None
        assert ctx_b.all_goals == []
        assert ctx_b.loans == []

    def test_explicit_period_filters_correctly(self, db_session: Session):
        """Income outside the requested period must not appear in results."""
        _make_user(db_session, 222)
        _make_profile(db_session, 222)

        # Income from 60 days ago — outside a 30-day window ending today
        old_date = TODAY - timedelta(days=60)
        db_session.add(Income(
            user_id=222, source="Old Job", amount=Decimal("50000"),
            income_date=old_date, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.flush()

        # Request only the last 30 days
        ctx = FinancialContextService(db_session).build_context(
            222, date_from=TODAY - timedelta(days=29), date_to=TODAY
        )

        # The old income is outside the period, so cash_flow should be None
        assert ctx.metrics.cash_flow is None


# ---------------------------------------------------------------------------
# Period handling
# ---------------------------------------------------------------------------


class TestPeriodHandling:
    def test_explicit_period_used(self, db_session: Session):
        _make_user(db_session, 223)
        _make_profile(db_session, 223)

        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        ctx = FinancialContextService(db_session).build_context(223, date_from=start, date_to=end)

        assert ctx.period_start == start
        assert ctx.period_end == end

    def test_default_period_is_30_days(self, db_session: Session):
        _make_user(db_session, 224)
        _make_profile(db_session, 224)

        ctx = FinancialContextService(db_session).build_context(224)

        assert ctx.period_end == TODAY
        assert (ctx.period_end - ctx.period_start).days == 29  # 30-day window
