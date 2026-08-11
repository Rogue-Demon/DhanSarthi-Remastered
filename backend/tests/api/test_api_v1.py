"""API integration tests for DhanSarthi REST API (Phase 6).

Tests all CRUD endpoints, ownership isolation, financial engine analytics
endpoints, and OpenAPI schema generation via FastAPI TestClient against
an in-memory SQLite database.
"""

import os

# Must be set before any app module import.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import all models to register tables on Base.metadata
import app.models
from app.core.database import Base, SessionLocal, engine, get_db
from fastapi import Request
from app.api.deps import get_current_user_id
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------




@pytest.fixture()
def db() -> Session:
    """Provide a clean, transactional database session per test."""
    session = SessionLocal()
    session.begin()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """TestClient wired to the per-test transactional session.

    Overrides ``get_current_user_id`` to read from ``X-User-ID`` header
    so existing tests that use ``HEADERS_USER1`` / ``HEADERS_USER2``
    continue to pass without requiring real JWT tokens.
    """

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    def _override_get_current_user_id(request: Request) -> int:
        """Read X-User-ID header so HEADERS_USER1/HEADERS_USER2 tests work."""
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


def _seed_user(db: Session, user_id: int = 1) -> None:
    """Insert a minimal User row required by FK constraints."""
    from app.models.user import User

    existing = db.get(User, user_id)
    if existing is None:
        user = User(
            id=user_id,
            email=f"user{user_id}@test.com",
            password_hash="$2b$12$placeholder_hash_for_tests_only",
        )
        db.add(user)
        db.flush()


HEADERS_USER1 = {"X-User-ID": "1"}
HEADERS_USER2 = {"X-User-ID": "2"}



# ===================================================================
# OpenAPI Schema
# ===================================================================


class TestOpenAPISchema:
    """Verify that the OpenAPI schema generates without errors."""

    def test_openapi_json_returns_200(self, client: TestClient):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        data = r.json()
        assert "paths" in data
        paths = list(data["paths"].keys())
        for prefix in [
            "/api/v1/profile",
            "/api/v1/income",
            "/api/v1/expenses",
            "/api/v1/transactions",
            "/api/v1/assets",
            "/api/v1/liabilities",
            "/api/v1/investments",
            "/api/v1/loans",
            "/api/v1/goals",
            "/api/v1/budgets",
        ]:
            assert any(p.startswith(prefix) for p in paths), f"Missing {prefix}"


# ===================================================================
# Profile
# ===================================================================


class TestProfileAPI:

    def test_create_and_get_profile(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        payload = {
            "persona": "PROFESSIONAL",
            "display_name": "Nitesh Kumar",
            "country": "IN",
            "currency": "INR",
        }
        r = client.post("/api/v1/profile", json=payload, headers=HEADERS_USER1)
        assert r.status_code in (200, 201)

        r2 = client.get("/api/v1/profile", headers=HEADERS_USER1)
        assert r2.status_code == 200


# ===================================================================
# Income CRUD
# ===================================================================


class TestIncomeAPI:

    def test_income_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "source": "Salary",
            "amount": "75000.00",
            "income_date": str(date.today()),
            "category": "SALARY",
            "frequency": "MONTHLY",
        }
        r = client.post("/api/v1/income", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        income_id = r.json()["id"]

        r = client.get(f"/api/v1/income/{income_id}", headers=HEADERS_USER1)
        assert r.status_code == 200
        assert r.json()["source"] == "Salary"

        r = client.get("/api/v1/income", headers=HEADERS_USER1)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

        r = client.patch(
            f"/api/v1/income/{income_id}",
            json={"amount": "80000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/income/{income_id}", headers=HEADERS_USER1)
        assert r.status_code == 204

    def test_income_ownership_isolation(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        _seed_user(db, 2)

        payload = {
            "source": "Consulting",
            "amount": "50000",
            "income_date": str(date.today()),
            "category": "FREELANCE",
            "frequency": "MONTHLY",
        }
        r = client.post("/api/v1/income", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        income_id = r.json()["id"]

        r2 = client.get(f"/api/v1/income/{income_id}", headers=HEADERS_USER2)
        assert r2.status_code == 404


# ===================================================================
# Expenses CRUD
# ===================================================================


class TestExpenseAPI:

    def test_expense_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "category": "FOOD",
            "amount": "3500.00",
            "expense_date": str(date.today()),
            "description": "Grocery shopping",
        }
        r = client.post("/api/v1/expenses", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        eid = r.json()["id"]

        r = client.get(f"/api/v1/expenses/{eid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/expenses", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/expenses/{eid}",
            json={"amount": "4000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/expenses/{eid}", headers=HEADERS_USER1)
        assert r.status_code == 204


# ===================================================================
# Transactions CRUD
# ===================================================================


class TestTransactionAPI:

    def test_transaction_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "transaction_type": "EXPENSE",
            "amount": "5000.00",
            "transaction_date": str(date.today()),
            "category": "CASH",
            "description": "ATM Withdrawal",
        }
        r = client.post("/api/v1/transactions", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        tid = r.json()["id"]

        r = client.get(f"/api/v1/transactions/{tid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/transactions", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.delete(f"/api/v1/transactions/{tid}", headers=HEADERS_USER1)
        assert r.status_code == 204


# ===================================================================
# Assets CRUD
# ===================================================================


class TestAssetAPI:

    def test_asset_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "name": "Savings Account",
            "asset_type": "BANK_BALANCE",
            "current_value": "250000.00",
            "valuation_date": str(date.today()),
        }
        r = client.post("/api/v1/assets", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        aid = r.json()["id"]
        assert Decimal(str(r.json()["current_value"])) == Decimal("250000.00")

        r = client.get(f"/api/v1/assets/{aid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/assets", headers=HEADERS_USER1)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

        r = client.patch(
            f"/api/v1/assets/{aid}",
            json={"current_value": "300000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/assets/{aid}", headers=HEADERS_USER1)
        assert r.status_code == 204

    def test_asset_ownership_isolation(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        _seed_user(db, 2)

        payload = {
            "name": "Gold Coins",
            "asset_type": "GOLD",
            "current_value": "100000.00",
        }
        r = client.post("/api/v1/assets", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        aid = r.json()["id"]

        r2 = client.get(f"/api/v1/assets/{aid}", headers=HEADERS_USER2)
        assert r2.status_code == 404


# ===================================================================
# Liabilities CRUD
# ===================================================================


class TestLiabilityAPI:

    def test_liability_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "name": "Credit Card Balance",
            "liability_type": "CREDIT_CARD",
            "outstanding_balance": "45000.00",
            "interest_rate_percent": "18.00",
        }
        r = client.post("/api/v1/liabilities", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        lid = r.json()["id"]

        r = client.get(f"/api/v1/liabilities/{lid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/liabilities", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/liabilities/{lid}",
            json={"outstanding_balance": "40000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/liabilities/{lid}", headers=HEADERS_USER1)
        assert r.status_code == 204


# ===================================================================
# Investments CRUD
# ===================================================================


class TestInvestmentAPI:

    def test_investment_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "name": "HDFC Equity Fund",
            "investment_type": "MUTUAL_FUND",
            "invested_amount": "100000.00",
            "current_value": "115000.00",
            "units": "500.0",
            "purchase_date": "2024-01-15",
        }
        r = client.post("/api/v1/investments", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        inv_id = r.json()["id"]

        r = client.get(f"/api/v1/investments/{inv_id}", headers=HEADERS_USER1)
        assert r.status_code == 200
        assert r.json()["name"] == "HDFC Equity Fund"

        r = client.get("/api/v1/investments", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/investments/{inv_id}",
            json={"current_value": "120000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/investments/{inv_id}", headers=HEADERS_USER1)
        assert r.status_code == 204

    def test_investment_transactions(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        r = client.post(
            "/api/v1/investments",
            json={
                "name": "SBI Small Cap",
                "investment_type": "MUTUAL_FUND",
                "invested_amount": "50000",
                "current_value": "55000",
                "purchase_date": "2024-06-01",
            },
            headers=HEADERS_USER1,
        )
        assert r.status_code == 201
        inv_id = r.json()["id"]

        r = client.post(
            f"/api/v1/investments/{inv_id}/transactions",
            json={
                "transaction_type": "BUY",
                "amount": "10000",
                "transaction_date": "2024-07-01",
                "units": "50.5",
                "price_per_unit": "198.02",
            },
            headers=HEADERS_USER1,
        )
        assert r.status_code == 201
        txn_id = r.json()["id"]

        r = client.get(
            f"/api/v1/investments/{inv_id}/transactions",
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

        r = client.get(
            f"/api/v1/investments/{inv_id}/transactions/{txn_id}",
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

    def test_investment_ownership_isolation(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        _seed_user(db, 2)

        r = client.post(
            "/api/v1/investments",
            json={
                "name": "Private Stock",
                "investment_type": "STOCK",
                "invested_amount": "200000",
                "current_value": "250000",
                "purchase_date": "2024-01-01",
            },
            headers=HEADERS_USER1,
        )
        assert r.status_code == 201
        inv_id = r.json()["id"]

        r2 = client.get(f"/api/v1/investments/{inv_id}", headers=HEADERS_USER2)
        assert r2.status_code == 404


# ===================================================================
# Loans CRUD
# ===================================================================


class TestLoanAPI:

    def test_loan_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "name": "Home Loan",
            "loan_type": "HOME",
            "principal_amount": "5000000.00",
            "interest_rate_percent": "8.50",
            "tenure_months": 240,
            "monthly_emi": "43391.00",
            "start_date": "2023-01-01",
            "lender": "SBI",
        }
        r = client.post("/api/v1/loans", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        loan_id = r.json()["id"]

        r = client.get(f"/api/v1/loans/{loan_id}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/loans", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.delete(f"/api/v1/loans/{loan_id}", headers=HEADERS_USER1)
        assert r.status_code == 204

    def test_loan_payments(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        r = client.post(
            "/api/v1/loans",
            json={
                "name": "Car Loan",
                "loan_type": "VEHICLE",
                "principal_amount": "800000",
                "interest_rate_percent": "9.25",
                "tenure_months": 60,
                "monthly_emi": "16600",
                "start_date": "2024-01-01",
            },
            headers=HEADERS_USER1,
        )
        assert r.status_code == 201
        loan_id = r.json()["id"]

        r = client.post(
            f"/api/v1/loans/{loan_id}/payments",
            json={
                "amount": "16600",
                "payment_date": "2024-02-01",
                "principal_component": "10000",
                "interest_component": "6600",
            },
            headers=HEADERS_USER1,
        )
        assert r.status_code == 201

        r = client.get(f"/api/v1/loans/{loan_id}/payments", headers=HEADERS_USER1)
        assert r.status_code == 200
        assert len(r.json()) >= 1


# ===================================================================
# Goals CRUD
# ===================================================================


class TestGoalAPI:

    def test_goal_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "title": "Emergency Fund",
            "target_amount": "600000.00",
            "current_amount": "100000.00",
            "target_date": "2025-12-31",
            "priority": 1,
        }
        r = client.post("/api/v1/goals", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        gid = r.json()["id"]
        assert r.json()["title"] == "Emergency Fund"

        r = client.get(f"/api/v1/goals/{gid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/goals", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/goals/{gid}",
            json={"current_amount": "150000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/goals/{gid}", headers=HEADERS_USER1)
        assert r.status_code == 204


# ===================================================================
# Budgets CRUD
# ===================================================================


class TestBudgetAPI:

    def test_budget_crud_lifecycle(self, client: TestClient, db: Session):
        _seed_user(db, 1)

        payload = {
            "category": "Food",
            "amount": "15000.00",
            "period": "MONTHLY",
            "start_date": str(date.today()),
        }
        r = client.post("/api/v1/budgets", json=payload, headers=HEADERS_USER1)
        assert r.status_code == 201
        bid = r.json()["id"]

        r = client.get(f"/api/v1/budgets/{bid}", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.get("/api/v1/budgets", headers=HEADERS_USER1)
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/budgets/{bid}",
            json={"amount": "18000.00"},
            headers=HEADERS_USER1,
        )
        assert r.status_code == 200

        r = client.delete(f"/api/v1/budgets/{bid}", headers=HEADERS_USER1)
        assert r.status_code == 204


# ===================================================================
# Financial Engine Endpoints
# ===================================================================


class TestFinancialEndpoints:

    def test_loan_calculate(self, client: TestClient):
        r = client.post(
            "/api/v1/financial/loan/calculate",
            json={
                "principal": "1000000",
                "annual_interest_rate_percent": "8.5",
                "tenure_months": 240,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "emi" in data or "monthly_emi" in data

    def test_sip_calculate(self, client: TestClient):
        r = client.post(
            "/api/v1/financial/investments/sip/calculate",
            json={
                "monthly_contribution": "10000",
                "expected_annual_return_percent": "12",
                "duration_years": "10",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "estimated_future_value" in data

    def test_financial_summary(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/summary", headers=HEADERS_USER1)
        assert r.status_code == 200
        data = r.json()
        assert "total_income" in data
        assert "net_worth" in data

    def test_cash_flow(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/cash-flow", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_savings(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/savings", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_net_worth(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/net-worth", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_debt_analysis(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/debt", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_investment_summary(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/investments/summary", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_budget_analysis(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/budget", headers=HEADERS_USER1)
        assert r.status_code == 200

    def test_goal_analysis(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/financial/goals", headers=HEADERS_USER1)
        assert r.status_code == 200


# ===================================================================
# Pagination
# ===================================================================


class TestPagination:

    def test_pagination_envelope_structure(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/income?page=1&page_size=5", headers=HEADERS_USER1)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data
        assert "total_pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 5


# ===================================================================
# Error Cases
# ===================================================================


class TestErrorCases:

    def test_get_nonexistent_resource_returns_404(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.get("/api/v1/income/999999", headers=HEADERS_USER1)
        assert r.status_code == 404

    def test_delete_nonexistent_resource_returns_404(self, client: TestClient, db: Session):
        _seed_user(db, 1)
        r = client.delete("/api/v1/assets/999999", headers=HEADERS_USER1)
        assert r.status_code == 404

    def test_invalid_loan_calculate_returns_422(self, client: TestClient):
        r = client.post("/api/v1/financial/loan/calculate", json={})
        assert r.status_code == 422

    def test_negative_amount_returns_422(self, client: TestClient):
        r = client.post(
            "/api/v1/financial/investments/sip/calculate",
            json={
                "monthly_contribution": "-1000",
                "expected_annual_return_percent": "12",
                "duration_years": "10",
            },
        )
        assert r.status_code == 422
