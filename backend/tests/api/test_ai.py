"""
Integration tests for the AI Advisor REST API — Phase 9.

Verifies:
  - POST /api/v1/ai/advisor endpoint contracts.
  - Unauthenticated requests are blocked (401).
  - Authenticated queries yield correct response schemas.
  - Custom exceptions (Safety violation, config error) map to correct HTTP codes.
"""

from __future__ import annotations

from decimal import Decimal
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user_id, get_llm_provider
from app.models.enums import Persona, RiskProfile
from app.models.profile import Profile
from app.models.user import User
from app.ai.providers.mock import MockLLMProvider
from app.ai.exceptions import AISafetyError, AIConfigurationError, AIProviderError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(db_session: Session) -> Session:
    return db_session


@pytest.fixture()
def client(db: Session) -> TestClient:
    """TestClient overrides deps to read user ID from request headers."""

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


HEADERS_USER = {"X-User-ID": "501"}


def _seed_user(db: Session, user_id: int) -> None:
    existing = db.get(User, user_id)
    if existing is None:
        u = User(
            id=user_id,
            email=f"ai_api_test_{user_id}@example.com",
            password_hash="$2b$12$placeholder",
        )
        db.add(u)

    if db.query(Profile).filter_by(user_id=user_id).first() is None:
        p = Profile(
            user_id=user_id,
            display_name=f"AI Test User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
        db.add(p)

    db.flush()


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


class TestAIAdvisorAPI:
    def test_unauthenticated_post_returns_401(self):
        """Requests lacking authentication header must return 401."""
        with TestClient(app) as anonymous_client:
            r = anonymous_client.post(
                "/api/v1/ai/advisor",
                json={"message": "Can I afford a loan?"},
            )
        assert r.status_code == 401

    def test_authenticated_post_returns_advisor_response(self, client: TestClient, db: Session):
        """Valid query returns a successful 200 payload with disclaimer and sources."""
        _seed_user(db, 501)

        # Override LLM provider with mock to avoid network dependency on HuggingFace.
        # The singleton introduced in L.7.3 means get_llm_provider() may return a
        # real HuggingFaceProvider cached from a previous test, which fails without network.
        def _get_mock_llm():
            return MockLLMProvider()

        app.dependency_overrides[get_llm_provider] = _get_mock_llm

        try:
            payload = {"message": "How can I set up a monthly budget?"}
            r = client.post("/api/v1/ai/advisor", json=payload, headers=HEADERS_USER)

            assert r.status_code == 200
            body = r.json()

            assert "response" in body
            assert "conversation_id" in body
            assert "sources" in body
            assert "disclaimer" in body
            assert "DhanSarthi" in body["disclaimer"]
        finally:
            app.dependency_overrides.pop(get_llm_provider, None)

    def test_safety_check_failure_returns_400(self, client: TestClient, db: Session):
        """A response triggering safety violations returns a clean 400 Bad Request."""
        _seed_user(db, 501)

        # Inject Mock LLM provider that yields a transaction execution claim
        def _get_unsafe_mock_llm():
            return MockLLMProvider("I have transferred 5000 from your account to mine.")

        app.dependency_overrides[get_llm_provider] = _get_unsafe_mock_llm

        payload = {"message": "Make a transfer."}
        r = client.post("/api/v1/ai/advisor", json=payload, headers=HEADERS_USER)

        # Should map to HTTP 400 due to exception handler
        assert r.status_code == 400
        assert "Safety boundary check failed" in r.json()["detail"]

        app.dependency_overrides.pop(get_llm_provider, None)

    def test_configuration_failure_returns_500(self, client: TestClient, db: Session):
        """Misconfigured provider keys return 500 Internal Server Error."""
        _seed_user(db, 501)

        def _get_misconfigured_mock_llm():
            # Class constructor simulating credential failures
            raise AIConfigurationError("Hugging Face API key is missing.")

        app.dependency_overrides[get_llm_provider] = _get_misconfigured_mock_llm

        payload = {"message": "Ask model."}
        r = client.post("/api/v1/ai/advisor", json=payload, headers=HEADERS_USER)

        assert r.status_code == 500
        assert "AI Advisor is misconfigured" in r.json()["detail"]

        app.dependency_overrides.pop(get_llm_provider, None)
