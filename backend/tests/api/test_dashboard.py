"""
Integration tests for the Dashboard API — Phase 8.

Tests cover:
  - GET /api/v1/dashboard
  - GET /api/v1/financial/context

Both endpoints use JWT authentication via the existing test override pattern.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.models.enums import (
    AssetType,
    GoalStatus,
    IncomeFrequency,
    LoanStatus,
    LoanType,
    Persona,
    RiskProfile,
)
from app.models.asset import Asset
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.goal import Goal
from app.models.income import Income
from app.models.investment import Investment
from app.models.liability import Liability
from app.models.loan import Loan
from app.models.profile import Profile
from app.models.user import User
from fastapi import Request

TODAY = date.today()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(db_session: Session) -> Session:
    return db_session


@pytest.fixture()
def client(db: Session) -> TestClient:
    """TestClient with per-test transactional session and header-driven user_id."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    def _override_get_current_user_id(request: Request) -> int:
        raw = request.headers.get("X-User-ID", "1")
        try:
            return int(raw)
        except ValueError:
            return 1

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


HEADERS_USER1 = {"X-User-ID": "300"}
HEADERS_USER2 = {"X-User-ID": "301"}


def _seed_user(db: Session, user_id: int) -> None:
    existing = db.get(User, user_id)
    if existing is None:
        u = User(
            id=user_id,
            email=f"dash_test_{user_id}@example.com",
            password_hash="$2b$12$placeholder",
        )
        db.add(u)

    if db.query(Profile).filter_by(user_id=user_id).first() is None:
        p = Profile(
            user_id=user_id,
            display_name=f"Dashboard User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
        db.add(p)

    db.flush()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestDashboardAuth:
    def test_unauthenticated_dashboard_returns_401(self):
        """Requests without Authorization header must be rejected."""
        with TestClient(app) as unauthenticated_client:
            r = unauthenticated_client.get("/api/v1/dashboard")
        assert r.status_code == 401

    def test_unauthenticated_context_returns_401(self):
        with TestClient(app) as unauthenticated_client:
            r = unauthenticated_client.get("/api/v1/financial/context")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Empty user
# ---------------------------------------------------------------------------


class TestDashboardEmptyUser:
    def test_empty_user_returns_200(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_empty_user_response_structure(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        assert "context_version" in body
        assert body["context_version"] == "1"
        assert "period" in body
        assert "user" in body
        assert "summary" in body
        assert "cash_flow" in body
        assert "net_worth" in body
        assert "investments" in body
        assert "loans" in body
        assert "debt" in body
        assert "goals" in body
        assert "budgets" in body
        assert "financial_health" in body

    def test_empty_user_has_data_flags_false(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        assert body["cash_flow"]["has_data"] is False
        assert body["net_worth"]["has_data"] is False
        assert body["investments"]["has_data"] is False
        assert body["loans"]["has_data"] is False
        assert body["debt"]["has_data"] is False
        assert body["goals"]["has_data"] is False
        assert body["budgets"]["has_data"] is False

    def test_empty_user_savings_rate_is_null(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()
        assert body["cash_flow"]["savings_rate_percent"] is None

    def test_empty_user_dti_is_null(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()
        assert body["debt"]["dti_percent"] is None

    def test_user_context_no_secrets(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()
        user = body["user"]
        assert "password" not in user
        assert "password_hash" not in user
        assert "token" not in user
        assert "jwt" not in user


# ---------------------------------------------------------------------------
# Cash flow
# ---------------------------------------------------------------------------


class TestDashboardCashFlow:
    def test_income_appears_in_cash_flow(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Income(
            user_id=300, source="Salary", amount=Decimal("100000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        cf = body["cash_flow"]
        assert cf["has_data"] is True
        assert Decimal(cf["total_income"]) == Decimal("100000")
        assert cf["savings_rate_percent"] is not None

    def test_savings_equals_income_minus_expenses(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Income(
            user_id=300, source="Job", amount=Decimal("80000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db.add(Expense(
            user_id=300, category="RENT", amount=Decimal("20000"),
            expense_date=TODAY, description="Rent",
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        assert Decimal(body["cash_flow"]["savings"]) == Decimal("60000")


# ---------------------------------------------------------------------------
# Net worth
# ---------------------------------------------------------------------------


class TestDashboardNetWorth:
    def test_net_worth_calculation(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Asset(
            user_id=300, name="Bank", asset_type=AssetType.BANK_BALANCE,
            value=Decimal("500000"), valuation_date=TODAY,
        ))
        db.add(Liability(
            user_id=300, name="Credit Card",
            liability_type="CREDIT_CARD", outstanding_amount=Decimal("50000"),
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        nw = body["net_worth"]
        assert nw["has_data"] is True
        assert Decimal(nw["net_worth"]) == Decimal("450000")
        assert Decimal(nw["total_assets"]) == Decimal("500000")
        assert Decimal(nw["total_liabilities"]) == Decimal("50000")


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------


class TestDashboardInvestments:
    def test_investment_summary(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Investment(
            user_id=300, name="Nifty ETF", investment_type="ETF",
            principal=Decimal("100000"), current_value=Decimal("120000"),
            purchase_date=TODAY - timedelta(days=180),
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        inv = body["investments"]
        assert inv["has_data"] is True
        assert Decimal(inv["total_invested"]) == Decimal("100000")
        assert Decimal(inv["current_value"]) == Decimal("120000")
        assert Decimal(inv["total_gain_loss"]) == Decimal("20000")


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------


class TestDashboardLoans:
    def test_loan_summary(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Loan(
            user_id=300, loan_type=LoanType.PERSONAL, lender="ICICI Bank",
            principal_amount=Decimal("500000"), outstanding_amount=Decimal("350000"),
            currency="INR", interest_rate=Decimal("0.12"),
            tenure=60, status=LoanStatus.ACTIVE,
            start_date=TODAY - timedelta(days=365),
            emi=Decimal("11000"),
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        loans = body["loans"]
        assert loans["has_data"] is True
        assert loans["loan_count"] == 1
        assert Decimal(loans["total_outstanding"]) == Decimal("350000")
        # interest_rate 0.12 → 12.00 %
        assert Decimal(loans["loans"][0]["interest_rate_percent"]) == Decimal("12.00")


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


class TestDashboardGoals:
    def test_goal_summary(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Goal(
            user_id=300, name="Emergency Fund", target_amount=Decimal("200000"),
            current_amount=Decimal("50000"), currency="INR",
            target_date=TODAY + timedelta(days=365), status=GoalStatus.ACTIVE, priority=1,
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        goals = body["goals"]
        assert goals["has_data"] is True
        assert goals["total_goals"] == 1
        assert goals["active_count"] == 1
        assert Decimal(goals["goals"][0]["completion_percentage"]) == Decimal("25.00")


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------


class TestDashboardBudgets:
    def test_budget_summary(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Budget(
            user_id=300, category="FOOD",
            amount=Decimal("10000"), period="MONTHLY",
            start_date=TODAY - timedelta(days=15),
        ))
        db.add(Expense(
            user_id=300, category="FOOD", amount=Decimal("8000"),
            expense_date=TODAY, description="Groceries",
        ))
        db.flush()

        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        budgets = body["budgets"]
        assert budgets["has_data"] is True
        assert Decimal(budgets["total_budget"]) == Decimal("10000")
        assert Decimal(budgets["total_spending"]) == Decimal("8000")
        assert Decimal(budgets["overall_utilization_percent"]) == Decimal("80.00")


# ---------------------------------------------------------------------------
# Period
# ---------------------------------------------------------------------------


class TestDashboardPeriod:
    def test_default_period_structure(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        period = body["period"]
        assert "start_date" in period
        assert "end_date" in period
        assert "period_days" in period
        assert period["end_date"] == TODAY.isoformat()
        assert period["period_days"] == 30

    def test_explicit_period_is_used(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        start = "2026-01-01"
        end = "2026-01-31"
        r = client.get(
            f"/api/v1/dashboard?date_from={start}&date_to={end}",
            headers=HEADERS_USER1,
        )
        body = r.json()

        assert body["period"]["start_date"] == start
        assert body["period"]["end_date"] == end
        assert body["period"]["period_days"] == 31


# ---------------------------------------------------------------------------
# Ownership isolation
# ---------------------------------------------------------------------------


class TestDashboardOwnership:
    def test_user_a_data_not_visible_to_user_b(self, client: TestClient, db: Session):
        """Critical: User A's income must not appear in User B's dashboard."""
        _seed_user(db, 300)
        _seed_user(db, 301)

        # User A has significant income
        db.add(Income(
            user_id=300, source="Big Salary", amount=Decimal("500000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db.add(Asset(
            user_id=300, name="Property", asset_type=AssetType.PROPERTY,
            value=Decimal("10000000"), valuation_date=TODAY,
        ))
        db.flush()

        # User B's dashboard
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER2)
        assert r.status_code == 200
        body = r.json()

        # User B should have no data
        assert body["cash_flow"]["has_data"] is False
        assert body["net_worth"]["has_data"] is False
        assert Decimal(body["summary"]["total_income"]) == Decimal("0")
        assert Decimal(body["summary"]["total_assets"]) == Decimal("0")

    def test_user_b_data_not_visible_to_user_a(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        _seed_user(db, 301)

        # User B has data
        db.add(Investment(
            user_id=301, name="User B ETF", investment_type="ETF",
            principal=Decimal("200000"), current_value=Decimal("250000"),
            purchase_date=TODAY - timedelta(days=90),
        ))
        db.flush()

        # User A's dashboard
        r = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        body = r.json()

        assert body["investments"]["has_data"] is False


# ---------------------------------------------------------------------------
# Financial context endpoint
# ---------------------------------------------------------------------------


class TestFinancialContextEndpoint:
    def test_context_endpoint_returns_200(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/financial/context", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_context_has_version_field(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/financial/context", headers=HEADERS_USER1)
        body = r.json()
        assert body["context_version"] == "1"

    def test_context_no_secrets(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        r = client.get("/api/v1/financial/context", headers=HEADERS_USER1)
        body_str = r.text.lower()
        assert "password" not in body_str
        assert "password_hash" not in body_str

    def test_context_unauthenticated_returns_401(self):
        with TestClient(app) as c:
            r = c.get("/api/v1/financial/context")
        assert r.status_code == 401

    def test_context_same_data_as_dashboard(self, client: TestClient, db: Session):
        _seed_user(db, 300)
        db.add(Income(
            user_id=300, source="Consulting", amount=Decimal("75000"),
            income_date=TODAY, category="FREELANCE", frequency=IncomeFrequency.MONTHLY,
        ))
        db.flush()

        r_dash = client.get("/api/v1/dashboard", headers=HEADERS_USER1)
        r_ctx = client.get("/api/v1/financial/context", headers=HEADERS_USER1)

        dash = r_dash.json()
        ctx = r_ctx.json()

        # Both endpoints should return the same financial data
        assert dash["summary"]["total_income"] == ctx["summary"]["total_income"]
        assert dash["cash_flow"]["total_income"] == ctx["cash_flow"]["total_income"]
