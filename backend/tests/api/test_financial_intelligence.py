"""
Integration tests for the Financial Intelligence REST API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


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
        json={"email": "intela@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "intela@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    # User B
    client.post(
        "/api/v1/auth/register",
        json={"email": "intelb@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "intelb@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


class TestFinancialIntelligenceAPI:
    def test_summary_and_analytical_endpoints(self, client: TestClient, auth_headers: dict):
        # 1. Fetch summary as User A (no data seeded yet -> insufficient data)
        resp = client.get(
            "/api/v1/financial-intelligence/summary",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_quality"] == "LIMITED"
        assert data["cash_flow"]["status"] == "INSUFFICIENT_DATA"

        # 2. Fetch specific metric endpoints
        cf_resp = client.get(
            "/api/v1/financial-intelligence/cash-flow",
            headers=auth_headers["user_a"],
        )
        assert cf_resp.status_code == 200
        assert cf_resp.json()["metric"] == "net_cash_flow"

        debt_resp = client.get(
            "/api/v1/financial-intelligence/debt",
            headers=auth_headers["user_a"],
        )
        assert debt_resp.status_code == 200
        assert debt_resp.json()["metric"] == "debt_to_income"

    def test_loan_scenario_simulation(self, client: TestClient, auth_headers: dict):
        # Principal: 5 Lakhs, Interest: 9.5%, Tenure: 3 years (36 months)
        req_payload = {
            "principal": 500000.00,
            "annual_interest_rate_percent": 9.50,
            "tenure_months": 36,
        }
        resp = client.post(
            "/api/v1/financial-intelligence/loan-scenario",
            headers=auth_headers["user_a"],
            json=req_payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["emi"]) > 0
        assert "INSUFFICIENT_DATA" in data["risk_flags"]  # No income seeded, DTI cannot be checked

    def test_loan_scenario_invalid_bounds(self, client: TestClient, auth_headers: dict):
        # Case 1: Negative principal
        req_payload = {
            "principal": -1000.00,
            "annual_interest_rate_percent": 10.00,
            "tenure_months": 24,
        }
        resp = client.post(
            "/api/v1/financial-intelligence/loan-scenario",
            headers=auth_headers["user_a"],
            json=req_payload,
        )
        assert resp.status_code == 422

        # Case 2: Zero tenure
        req_payload = {
            "principal": 100000.00,
            "annual_interest_rate_percent": 10.00,
            "tenure_months": 0,
        }
        resp = client.post(
            "/api/v1/financial-intelligence/loan-scenario",
            headers=auth_headers["user_a"],
            json=req_payload,
        )
        assert resp.status_code == 422

    def test_generic_scenario_simulators(self, client: TestClient, auth_headers: dict):
        # 1. Savings reduction scenario
        req_payload = {
            "scenario_type": "SAVINGS",
            "params": {"expense_reduction": 5000.00},
        }
        resp = client.post(
            "/api/v1/financial-intelligence/scenario",
            headers=auth_headers["user_a"],
            json=req_payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["difference"]) == 5000.00

        # 2. SIP compound growth scenario
        req_payload = {
            "scenario_type": "INVESTMENT_GROWTH",
            "params": {
                "monthly_contribution": 10000.00,
                "expected_annual_return_percent": 12.00,
                "duration_years": 10,
            },
        }
        resp = client.post(
            "/api/v1/financial-intelligence/scenario",
            headers=auth_headers["user_a"],
            json=req_payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["scenario_value"]) > float(data["base_value"])  # Compound growth produces surplus returns
