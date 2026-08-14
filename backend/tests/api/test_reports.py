"""
Unit and integration tests for DhanSarthi Financial Reports API.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.enums import FinancialReportType


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient overriding get_db dependency."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register and login a test user, returning Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "report_user@test.com", "password": "password123"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "report_user@test.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



def test_export_report_pdf(client: TestClient, auth_headers: dict):
    """Test PDF export endpoint returns valid application/pdf bytes."""
    response = client.get(
        "/api/v1/reports/export?report_type=monthly_executive&format=pdf",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_report_csv(client: TestClient, auth_headers: dict):
    """Test CSV export endpoint returns valid text/csv bytes."""
    response = client.get(
        "/api/v1/reports/export?report_type=expense_breakdown&format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "DhanSarthi Financial Report" in response.text
    assert ".csv" in response.headers["content-disposition"]


def test_export_report_xlsx(client: TestClient, auth_headers: dict):
    """Test XLSX export endpoint returns valid openxml spreadsheet bytes."""
    response = client.get(
        "/api/v1/reports/export?report_type=net_worth_statement&format=xlsx",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert ".xlsx" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_report_unauthorized(client: TestClient):
    """Test export endpoint requires authentication."""
    response = client.get("/api/v1/reports/export?report_type=monthly_executive&format=pdf")
    assert response.status_code == 401


def test_export_report_all_types(client: TestClient, auth_headers: dict):
    """Test all report types return successful 200 OK responses."""
    for report_type in [
        FinancialReportType.MONTHLY_EXECUTIVE,
        FinancialReportType.ANNUAL_TAX_SUMMARY,
        FinancialReportType.EXPENSE_BREAKDOWN,
        FinancialReportType.NET_WORTH_STATEMENT,
        FinancialReportType.GOAL_FEASIBILITY,
        FinancialReportType.DEBT_SNOWBALL,
    ]:
        response = client.get(
            f"/api/v1/reports/export?report_type={report_type.value}&format=csv",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.content) > 0


def test_export_report_cross_user_isolation(client: TestClient):
    """Verify User A's generated report contains ONLY User A data and not User B's data."""
    # Register User A
    client.post("/api/v1/auth/register", json={"email": "usera_report@test.com", "password": "password123"})
    login_a = client.post("/api/v1/auth/login", json={"email": "usera_report@test.com", "password": "password123"})
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # Register User B
    client.post("/api/v1/auth/register", json={"email": "userb_report@test.com", "password": "password123"})
    login_b = client.post("/api/v1/auth/login", json={"email": "userb_report@test.com", "password": "password123"},)
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # Add Income for User A
    client.post("/api/v1/income", json={"amount": "150000.00", "source": "UserA Secret Salary", "category": "Salary", "income_date": "2026-08-14"}, headers=headers_a)

    # Add Income for User B
    client.post("/api/v1/income", json={"amount": "50000.00", "source": "UserB Secret Bonus", "category": "Bonus", "income_date": "2026-08-14"}, headers=headers_b)

    # User A downloads CSV report
    resp_a = client.get("/api/v1/reports/export?report_type=expense_breakdown&format=csv", headers=headers_a)
    assert resp_a.status_code == 200
    assert "₹150,000.00" in resp_a.text or "150000" in resp_a.text
    assert "₹50,000.00" not in resp_a.text

    # User B downloads CSV report
    resp_b = client.get("/api/v1/reports/export?report_type=expense_breakdown&format=csv", headers=headers_b)
    assert resp_b.status_code == 200
    assert "₹50,000.00" in resp_b.text or "50000" in resp_b.text
    assert "₹150,000.00" not in resp_b.text



def test_export_report_date_range_filtering(client: TestClient, auth_headers: dict):
    """Test date range query parameters (date_from, date_to)."""
    response = client.get(
        "/api/v1/reports/export?report_type=monthly_executive&format=pdf&date_from=2026-01-01&date_to=2026-01-31",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.content) > 0

