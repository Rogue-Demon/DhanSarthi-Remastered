"""
Integration tests for the Live Financial Market Data REST API endpoints.
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
        json={"email": "marketa@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "marketa@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    # User B
    client.post(
        "/api/v1/auth/register",
        json={"email": "marketb@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "marketb@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


class TestMarketDataAPI:
    def test_market_quotes_and_searches(self, client: TestClient, auth_headers: dict):
        # 1. Fetch stock quote
        resp = client.get(
            "/api/v1/market/stocks/RELIANCE.NS",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "RELIANCE.NS"
        assert float(data["price"]) == 2550.00
        assert data["provider"] == "mock_stock_provider"

        # 2. Search stock
        resp = client.get(
            "/api/v1/market/stocks/search?q=RELIANCE",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["symbol"] == "RELIANCE.NS"

        # 3. Fetch mutual fund NAV
        resp = client.get(
            "/api/v1/market/mutual-funds/119063/nav",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scheme_id"] == "119063"
        assert float(data["nav"]) == 125.40

        # 4. Search mutual funds
        resp = client.get(
            "/api/v1/market/mutual-funds/search?q=SBI",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["scheme_id"] == "119063"

        # 5. Fetch FX rate
        resp = client.get(
            "/api/v1/market/fx/USD/INR",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_currency"] == "USD"
        assert data["quote_currency"] == "INR"
        assert float(data["rate"]) == 83.25

        # 6. Fetch index quote
        resp = client.get(
            "/api/v1/market/indices/SENSEX",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["index_name"] == "SENSEX"
        assert float(data["value"]) == 72500.00

        # 7. Fetch interest rate
        resp = client.get(
            "/api/v1/market/interest-rates/IN/Repo Rate",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["country"] == "IN"
        assert data["type_name"] == "Repo Rate"
        assert float(data["rate"]) == 6.50

    def test_estimated_portfolio_valuation(self, client: TestClient, auth_headers: dict):
        # Fetch estimated portfolio (user has no investments yet)
        resp = client.get(
            "/api/v1/market/portfolio/estimated",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_stored_value"]) == 0.0
        assert float(data["total_estimated_value"]) == 0.0
        assert len(data["items"]) == 0

    def test_input_validation_prevents_malformed_symbols(self, client: TestClient, auth_headers: dict):
        resp = client.get(
            "/api/v1/market/stocks/RELIANCE;DROP%20TABLE;",
            headers=auth_headers["user_a"],
        )
        assert resp.status_code == 400
