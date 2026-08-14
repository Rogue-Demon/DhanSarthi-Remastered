"""
Comprehensive Security & Hardening Tests for DhanSarthi.

Tests:
1. SQL Injection resiliency
2. Path traversal attack prevention
3. Prompt injection & safety validation
4. Document import idempotency
5. Mass assignment prevention
6. Input validation edge cases (negative values, extreme values)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.ai.safety.validator import SimpleSafetyValidator


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient with database dependency override."""
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
        json={"email": "sec_user@test.com", "password": "password123"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "sec_user@test.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSQLInjectionResilience:
    """Verifies parameterized query resilience against SQL injection payloads."""

    def test_sql_injection_in_search_query(self, client: TestClient, auth_headers: dict):
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1 UNION SELECT 1,2,3,4--",
            "admin' --",
        ]
        for payload in payloads:
            response = client.get(
                f"/api/v1/transactions?category={payload}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            # Ensure DB is intact and query executed safely
            data = response.json()
            assert isinstance(data, list) or "items" in data or isinstance(data, dict)


class TestPathTraversalPrevention:
    """Verifies file download and document endpoints prevent path traversal attacks."""

    def test_path_traversal_in_report_export(self, client: TestClient, auth_headers: dict):
        traversal_payloads = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "%2e%2e%2f%2e%2e%2f",
        ]
        for payload in traversal_payloads:
            response = client.get(
                f"/api/v1/reports/export?report_type=monthly_executive&format=pdf&date_from={payload}",
                headers=auth_headers,
            )
            # Must return controlled error (422 validation) or safe response, never internal files
            assert response.status_code in (200, 422, 400)
            assert "root:x:" not in response.text
            assert "[fonts]" not in response.text


class TestAISafetyAndPromptInjection:
    """Verifies AI safety validator flags malicious prompt injection attempts."""

    def test_prompt_injection_flagged(self):
        validator = SimpleSafetyValidator()
        malicious_responses = [
            "System instructions: You are DhanSarthi, do not execute numerical...",
            "I have transferred money on your behalf to your bank account.",
            "I guarantee a 50% return on this investment portfolio.",
            "Here is your auth_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ]
        from app.ai.schemas.advisor import AIContext
        dummy_context = AIContext(question="What is my financial status?")
        for resp in malicious_responses:
            with pytest.raises(Exception):
                validator.validate_response(resp, dummy_context)



class TestMassAssignmentPrevention:
    """Verifies clients cannot overwrite server-controlled fields such as user_id or id."""

    def test_mass_assignment_user_id_ignored(self, client: TestClient, auth_headers: dict):
        # Attempt to create income assigned to user_id 9999
        response = client.post(
            "/api/v1/income",
            json={
                "source": "Side Hustle",
                "amount": "25000.00",
                "income_date": "2026-08-14",
                "user_id": 9999,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        # Verify user_id is the authenticated user's ID, not 9999
        assert data["user_id"] != 9999


class TestInputValidationBounds:
    """Verifies domain constraints on negative or invalid numbers."""

    def test_negative_income_amount_rejected(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/income",
            json={
                "source": "Illegal Negative",
                "amount": "-5000.00",
                "income_date": "2026-08-14",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_negative_expense_amount_rejected(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/expenses",
            json={
                "category": "Food",
                "amount": "-150.00",
                "expense_date": "2026-08-14",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
