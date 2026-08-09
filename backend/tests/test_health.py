"""
Tests for FastAPI health endpoints.

Coverage
--------
* GET /health — application liveness (always 200, no DB required).
* GET /health/ready — database readiness (200 when DB reachable, 503 when not).
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# /health — liveness
# ---------------------------------------------------------------------------


class TestHealthLiveness:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_ok_status(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /health/ready — readiness (database reachable)
# ---------------------------------------------------------------------------


class TestHealthReadinessWhenDatabaseIsReachable:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_returns_ready_status(self, client: TestClient) -> None:
        response = client.get("/health/ready")
        assert response.json() == {"status": "ready"}


# ---------------------------------------------------------------------------
# /health/ready — readiness (database unavailable)
# ---------------------------------------------------------------------------


class TestHealthReadinessWhenDatabaseIsUnreachable:
    def test_returns_503_when_database_raises(self, client: TestClient) -> None:
        """When the engine raises SQLAlchemyError, the endpoint must return
        503 without exposing any internal database details.
        """
        fake_exc = OperationalError("connection refused", {}, None)

        with patch("app.main.engine.connect", side_effect=fake_exc):
            response = client.get("/health/ready")

        assert response.status_code == 503

    def test_error_body_contains_no_credentials(self, client: TestClient) -> None:
        """The 503 response must never include connection strings or credentials."""
        fake_exc = OperationalError(
            "postgresql+psycopg://admin:secret@db.prod:5432/data",
            {},
            None,
        )
        with patch("app.main.engine.connect", side_effect=fake_exc):
            response = client.get("/health/ready")

        body = response.text
        # Ensure the raw exception message (with credentials) is not leaked.
        assert "secret" not in body
        assert "psycopg" not in body
        assert "admin" not in body

    def test_error_body_is_generic(self, client: TestClient) -> None:
        fake_exc = OperationalError("anything", {}, None)
        with patch("app.main.engine.connect", side_effect=fake_exc):
            response = client.get("/health/ready")

        assert response.json() == {"detail": "Database is unavailable."}
