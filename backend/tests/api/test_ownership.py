"""Integration tests for cross-user data isolation and IDOR protection.

Verifies that User A cannot access or modify User B's financial resources,
including: Profile, Income, Expenses, Transactions, Assets, Liabilities,
Investments, Loans, Loan Payments, Goals, and Budgets.
"""

from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.user import User


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient that overrides the DB dependency only."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, dict[str, str]]:
    """Register and login two separate users, returning their Authorization headers."""
    # User A
    client.post(
        "/api/v1/auth/register",
        json={"email": "usera@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "usera@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    # User B
    client.post(
        "/api/v1/auth/register",
        json={"email": "userb@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "userb@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


def test_profile_isolation(client: TestClient, auth_headers: dict):
    # Fetch User A's profile
    resp_a = client.get("/api/v1/profile", headers=auth_headers["user_a"])
    assert resp_a.status_code == 200
    assert resp_a.json()["display_name"] == "usera"

    # Fetch User B's profile
    resp_b = client.get("/api/v1/profile", headers=auth_headers["user_b"])
    assert resp_b.status_code == 200
    assert resp_b.json()["display_name"] == "userb"

    # Modify User A's profile
    client.patch(
        "/api/v1/profile",
        headers=auth_headers["user_a"],
        json={"display_name": "NewUserA"},
    )

    # Verify User B's profile remains unchanged
    resp_b_check = client.get("/api/v1/profile", headers=auth_headers["user_b"])
    assert resp_b_check.json()["display_name"] == "userb"


def test_income_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates an income record
    create_resp = client.post(
        "/api/v1/income",
        headers=auth_headers["user_b"],
        json={
            "source": "Salary B",
            "amount": 5000.0,
            "category": "salary",
            "currency": "USD",
            "frequency": "MONTHLY",
            "income_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    income_id = create_resp.json()["id"]

    # User A attempts to retrieve User B's income
    get_resp = client.get(f"/api/v1/income/{income_id}", headers=auth_headers["user_a"])
    assert get_resp.status_code == 404

    # User A attempts to update User B's income
    patch_resp = client.patch(
        f"/api/v1/income/{income_id}",
        headers=auth_headers["user_a"],
        json={"amount": 99999.0},
    )
    assert patch_resp.status_code == 404

    # User A attempts to delete User B's income
    delete_resp = client.delete(f"/api/v1/income/{income_id}", headers=auth_headers["user_a"])
    assert delete_resp.status_code == 404


def test_expense_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates an expense
    create_resp = client.post(
        "/api/v1/expenses",
        headers=auth_headers["user_b"],
        json={
            "category": "Food B",
            "amount": 50.0,
            "currency": "USD",
            "expense_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    expense_id = create_resp.json()["id"]

    # User A attempts to access User B's expense
    assert client.get(f"/api/v1/expenses/{expense_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/expenses/{expense_id}", headers=auth_headers["user_a"], json={"amount": 10.0}).status_code == 404
    assert client.delete(f"/api/v1/expenses/{expense_id}", headers=auth_headers["user_a"]).status_code == 404


def test_transaction_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates a transaction
    create_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers["user_b"],
        json={
            "transaction_type": "EXPENSE",
            "amount": 25.0,
            "currency": "USD",
            "category": "Utilities",
            "transaction_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    txn_id = create_resp.json()["id"]

    # User A attempts to access User B's transaction
    assert client.get(f"/api/v1/transactions/{txn_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/transactions/{txn_id}", headers=auth_headers["user_a"], json={"amount": 10.0}).status_code == 404
    assert client.delete(f"/api/v1/transactions/{txn_id}", headers=auth_headers["user_a"]).status_code == 404


def test_asset_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates an asset
    create_resp = client.post(
        "/api/v1/assets",
        headers=auth_headers["user_b"],
        json={
            "asset_type": "GOLD",
            "name": "Gold Coins B",
            "current_value": 2000.0,
            "currency": "USD",
            "valuation_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    asset_id = create_resp.json()["id"]

    # User A attempts to access User B's asset
    assert client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/assets/{asset_id}", headers=auth_headers["user_a"], json={"current_value": 1.0}).status_code == 404
    assert client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers["user_a"]).status_code == 404


def test_liability_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates a liability
    create_resp = client.post(
        "/api/v1/liabilities",
        headers=auth_headers["user_b"],
        json={
            "liability_type": "CREDIT_CARD",
            "name": "Card B",
            "outstanding_balance": 500.0,
            "currency": "USD",
            "interest_rate_percent": 15.0,
        },
    )
    assert create_resp.status_code == 201
    liability_id = create_resp.json()["id"]

    # User A attempts to access User B's liability
    assert client.get(f"/api/v1/liabilities/{liability_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/liabilities/{liability_id}", headers=auth_headers["user_a"], json={"outstanding_balance": 0.0}).status_code == 404
    assert client.delete(f"/api/v1/liabilities/{liability_id}", headers=auth_headers["user_a"]).status_code == 404


def test_investment_and_transaction_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates an investment
    create_resp = client.post(
        "/api/v1/investments",
        headers=auth_headers["user_b"],
        json={
            "name": "Mutual Fund B",
            "investment_type": "MUTUAL_FUND",
            "invested_amount": 10000.0,
            "current_value": 11000.0,
        },
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # User B creates an investment transaction
    txn_resp = client.post(
        f"/api/v1/investments/{inv_id}/transactions",
        headers=auth_headers["user_b"],
        json={
            "transaction_type": "BUY",
            "amount": 1000.0,
            "transaction_date": str(date.today()),
            "units": 10.0,
            "price_per_unit": 100.0,
        },
    )
    assert txn_resp.status_code == 201
    txn_id = txn_resp.json()["id"]

    # User A attempts to access User B's investment
    assert client.get(f"/api/v1/investments/{inv_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/investments/{inv_id}", headers=auth_headers["user_a"], json={"current_value": 0.0}).status_code == 404

    # User A attempts to access User B's investment transactions
    assert client.get(f"/api/v1/investments/{inv_id}/transactions", headers=auth_headers["user_a"]).status_code == 404
    
    # Post with valid payload structure
    post_resp = client.post(
        f"/api/v1/investments/{inv_id}/transactions",
        headers=auth_headers["user_a"],
        json={
            "transaction_type": "BUY",
            "amount": 50.0,
            "transaction_date": str(date.today()),
            "units": 1.0,
            "price_per_unit": 50.0,
        },
    )
    assert post_resp.status_code == 404
    
    assert client.get(f"/api/v1/investments/{inv_id}/transactions/{txn_id}", headers=auth_headers["user_a"]).status_code == 404

    # Nested check: User A tries to pass their own investment ID, but User B's transaction ID
    create_a_resp = client.post(
        "/api/v1/investments",
        headers=auth_headers["user_a"],
        json={
            "name": "Mutual Fund A",
            "investment_type": "MUTUAL_FUND",
            "invested_amount": 1000.0,
            "current_value": 1000.0,
        },
    )
    inv_a_id = create_a_resp.json()["id"]
    nested_get = client.get(
        f"/api/v1/investments/{inv_a_id}/transactions/{txn_id}",
        headers=auth_headers["user_a"],
    )
    assert nested_get.status_code == 404

    # Finally, delete should protect User B
    assert client.delete(f"/api/v1/investments/{inv_id}", headers=auth_headers["user_a"]).status_code == 404


def test_loan_and_payment_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates a loan
    create_resp = client.post(
        "/api/v1/loans",
        headers=auth_headers["user_b"],
        json={
            "name": "Personal Loan B",
            "loan_type": "PERSONAL",
            "principal_amount": 5000.0,
            "interest_rate_percent": 12.0,
            "tenure_months": 12,
            "monthly_emi": 450.0,
            "start_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    loan_id = create_resp.json()["id"]

    # User B records a payment
    payment_resp = client.post(
        f"/api/v1/loans/{loan_id}/payments",
        headers=auth_headers["user_b"],
        json={
            "payment_date": str(date.today()),
            "amount": 500.0,
            "principal_component": 450.0,
            "interest_component": 50.0,
        },
    )
    assert payment_resp.status_code == 201
    payment_id = payment_resp.json()["id"]

    # User A attempts to access User B's loan
    assert client.get(f"/api/v1/loans/{loan_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/loans/{loan_id}", headers=auth_headers["user_a"], json={"principal_amount": 10.0}).status_code == 404

    # User A attempts to access User B's payments
    assert client.get(f"/api/v1/loans/{loan_id}/payments", headers=auth_headers["user_a"]).status_code == 404
    
    # Post with valid payload structure
    post_resp = client.post(
        f"/api/v1/loans/{loan_id}/payments",
        headers=auth_headers["user_a"],
        json={
            "payment_date": str(date.today()),
            "amount": 100.0,
        },
    )
    assert post_resp.status_code == 404
    
    assert client.get(f"/api/v1/loans/{loan_id}/payments/{payment_id}", headers=auth_headers["user_a"]).status_code == 404

    # Delete loan checks
    assert client.delete(f"/api/v1/loans/{loan_id}", headers=auth_headers["user_a"]).status_code == 404


def test_goal_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates a goal
    create_resp = client.post(
        "/api/v1/goals",
        headers=auth_headers["user_b"],
        json={
            "title": "Retirement B",
            "target_amount": 1000000.0,
            "current_amount": 10000.0,
            "currency": "USD",
            "priority": 1,
            "status": "ACTIVE",
        },
    )
    assert create_resp.status_code == 201
    goal_id = create_resp.json()["id"]

    # User A attempts to access User B's goal
    assert client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/goals/{goal_id}", headers=auth_headers["user_a"], json={"current_amount": 10.0}).status_code == 404
    assert client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers["user_a"]).status_code == 404


def test_budget_idor_protection(client: TestClient, auth_headers: dict):
    # User B creates a budget
    create_resp = client.post(
        "/api/v1/budgets",
        headers=auth_headers["user_b"],
        json={
            "category": "Food B",
            "amount": 500.0,
            "currency": "USD",
            "period": "MONTHLY",
            "start_date": str(date.today()),
        },
    )
    assert create_resp.status_code == 201
    budget_id = create_resp.json()["id"]

    # User A attempts to access User B's budget
    assert client.get(f"/api/v1/budgets/{budget_id}", headers=auth_headers["user_a"]).status_code == 404
    assert client.patch(f"/api/v1/budgets/{budget_id}", headers=auth_headers["user_a"], json={"amount": 10.0}).status_code == 404
    assert client.delete(f"/api/v1/budgets/{budget_id}", headers=auth_headers["user_a"]).status_code == 404


def test_financial_analytics_endpoints_use_token_user_id(client: TestClient, auth_headers: dict):
    # Retrieve User A's summary
    resp_a = client.get("/api/v1/financial/summary", headers=auth_headers["user_a"])
    assert resp_a.status_code == 200
    assert float(resp_a.json()["total_income"]) == 0.0

    # User B adds income
    client.post(
        "/api/v1/income",
        headers=auth_headers["user_b"],
        json={
            "source": "Salary B",
            "amount": 5000.0,
            "category": "salary",
            "currency": "USD",
            "frequency": "MONTHLY",
            "income_date": str(date.today()),
        },
    )

    # Verify User A's summary remains unchanged (0.0)
    resp_a_check = client.get("/api/v1/financial/summary", headers=auth_headers["user_a"])
    assert float(resp_a_check.json()["total_income"]) == 0.0

    # Verify User B's summary shows the new income
    resp_b = client.get("/api/v1/financial/summary", headers=auth_headers["user_b"])
    assert float(resp_b.json()["total_income"]) >= 5000.0


def test_investment_metadata_crud_and_merge(client: TestClient, auth_headers: dict):
    # User A creates an investment of type OTHER with metadata subtype 'PPF'
    payload = {
        "name": "My PPF Account",
        "investment_type": "OTHER",
        "invested_amount": 150000.0,
        "current_value": 150000.0,
        "ticker_symbol": "PPF-01",
        "institution": "SBI",
        "notes": "SBI Provident Fund",
        "investment_metadata": {
            "subtype": "PPF",
            "annual_contribution": 50000.0
        }
    }
    create_resp = client.post("/api/v1/investments", headers=auth_headers["user_a"], json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["investment_metadata"]["subtype"] == "PPF"
    assert created_data["investment_metadata"]["annual_contribution"] == 50000.0
    assert created_data["ticker_symbol"] == "PPF-01"
    
    inv_id = created_data["id"]

    # Retrieve and verify list filters
    list_resp = client.get("/api/v1/investments?investment_type=OTHER", headers=auth_headers["user_a"])
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) >= 1
    ppf_item = next(item for item in items if item["id"] == inv_id)
    assert ppf_item["investment_metadata"]["subtype"] == "PPF"

    # Update only the name and verify metadata remains completely intact
    patch_resp = client.patch(
        f"/api/v1/investments/{inv_id}",
        headers=auth_headers["user_a"],
        json={"name": "My Updated PPF Account"}
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["name"] == "My Updated PPF Account"
    assert patched_data["investment_metadata"]["subtype"] == "PPF"
    assert patched_data["investment_metadata"]["annual_contribution"] == 50000.0

    # Update metadata and verify custom keys are merged/preserved
    update_meta_resp = client.patch(
        f"/api/v1/investments/{inv_id}",
        headers=auth_headers["user_a"],
        json={
            "investment_metadata": {
                "subtype": "PPF",
                "annual_contribution": 75000.0,
                "extra_key": "custom_val"
            }
        }
    )
    assert update_meta_resp.status_code == 200
    updated_data = update_meta_resp.json()
    assert updated_data["investment_metadata"]["subtype"] == "PPF"
    assert updated_data["investment_metadata"]["annual_contribution"] == 75000.0
    assert updated_data["investment_metadata"]["extra_key"] == "custom_val"
    # Root level fields are still mapped from previous states
    assert updated_data["ticker_symbol"] == "PPF-01"
    assert updated_data["institution"] == "SBI"
