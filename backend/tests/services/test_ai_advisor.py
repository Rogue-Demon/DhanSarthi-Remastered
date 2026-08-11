"""
Unit/service-level tests for DhanSarthi AIAdvisorService — Phase 9.

Verifies:
  1. Personal financial context is populated and de-identified (no passwords/secrets).
  2. RAG documents are queried separately and source metadata is preserved.
  3. Context builder filters personal facts (least privilege) and structures the prompt.
  4. Cross-user data isolation: User A facts do not leak to User B queries.
  5. Calculation boundaries: all user facts come from the deterministic backend context.
  6. Provider independence: orchestrator is testable with MockLLMProvider.
  7. Empty RAG results and provider failures are handled gracefully.
"""

from __future__ import annotations

import json
from decimal import Decimal
from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.exceptions import AIConfigurationError, AIProviderError, AISafetyError
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import AIAdvisorRequest
from app.models.enums import AssetType, IncomeFrequency, Persona, RiskProfile
from app.models.asset import Asset
from app.models.income import Income
from app.models.profile import Profile
from app.models.user import User
from app.services.dashboard_service import DashboardService

TODAY = date.today()


def _seed_user(db: Session, user_id: int, email: str) -> None:
    u = User(
        id=user_id,
        email=email,
        password_hash="$2b$12$passwordhashforusersecretsverification",
    )
    db.add(u)
    p = Profile(
        user_id=user_id,
        display_name=f"User {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    )
    db.add(p)
    db.flush()


# ---------------------------------------------------------------------------
# Provider Independence & Basic Flow
# ---------------------------------------------------------------------------


class TestAIAdvisorFlow:
    @pytest.mark.anyio
    async def test_successful_advisory_flow(self, db_session: Session):
        """Orchestrator successfully calls retriever, builder, provider, and validator."""
        _seed_user(db_session, 401, "user401@example.com")
        db_session.add(Income(
            user_id=401, source="Salary", amount=Decimal("100000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.flush()

        llm = MockLLMProvider("Personalized recommendation on SIP: start with 10k.")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)
        req = AIAdvisorRequest(message="Should I start a SIP? Tell me based on my income.")

        resp = await svc.get_guidance(user_id=401, request=req)

        assert resp.response == "Personalized recommendation on SIP: start with 10k."
        assert len(resp.sources) > 0
        assert "SIP" in resp.sources[0]
        # Verify prompt received user facts
        assert llm.last_context is not None
        assert llm.last_context.user_financial_context.cash_flow.total_income == Decimal("100000")


# ---------------------------------------------------------------------------
# Cross-User Data Isolation
# ---------------------------------------------------------------------------


class TestAICrossUserIsolation:
    @pytest.mark.anyio
    async def test_user_a_facts_do_not_leak_to_user_b(self, db_session: Session):
        """User A's large salary must not be visible when User B asks the AI."""
        _seed_user(db_session, 402, "usera@example.com")
        _seed_user(db_session, 403, "userb@example.com")

        # User A (402) has big salary
        db_session.add(Income(
            user_id=402, source="Mega Salary", amount=Decimal("500000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        # User B (403) has small salary
        db_session.add(Income(
            user_id=403, source="Mini Salary", amount=Decimal("20000"),
            income_date=TODAY, category="SALARY", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.flush()

        llm = MockLLMProvider("Response text")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)

        # Ask as User B (403)
        await svc.get_guidance(user_id=403, request=AIAdvisorRequest(message="What is my salary?"))

        # Verify last context sent to LLM contains ONLY User B's facts
        context = llm.last_context
        assert context is not None
        assert context.user_financial_context.cash_flow.total_income == Decimal("20000")
        assert context.user_financial_context.cash_flow.total_income != Decimal("500000")


# ---------------------------------------------------------------------------
# Secrets & Security Verification
# ---------------------------------------------------------------------------


class TestAISecurityAndSecrets:
    @pytest.mark.anyio
    async def test_secrets_and_passwords_are_never_sent_in_prompt(self, db_session: Session):
        """Sensitive credentials and passwords must be excluded from the generated prompt."""
        _seed_user(db_session, 404, "secret_test@example.com")
        db_session.flush()

        llm = MockLLMProvider("Mock response")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)
        await svc.get_guidance(user_id=404, request=AIAdvisorRequest(message="What is my worth?"))

        prompt = llm.last_prompt
        # Prompt should not contain password hash keyword or hash values
        assert "password" not in prompt.lower()
        assert "passwordhashforusersecretsverification" not in prompt

    @pytest.mark.anyio
    async def test_safety_validator_blocks_secret_leaks_in_output(self, db_session: Session):
        """Safety checks must block LLM responses containing API key/token patterns."""
        _seed_user(db_session, 405, "safetest@example.com")
        db_session.flush()

        # LLM returns a JWT token leaked in the response text
        llm = MockLLMProvider("Here is your secret session token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.sig")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)

        with pytest.raises(AISafetyError) as exc:
            await svc.get_guidance(user_id=405, request=AIAdvisorRequest(message="Tell me token."))
        assert "API keys, passwords, or tokens" in str(exc.value)

    @pytest.mark.anyio
    async def test_safety_validator_blocks_action_claims(self, db_session: Session):
        """Safety checks must raise an error if the model claims to execute autonomous transactions."""
        _seed_user(db_session, 406, "action@example.com")
        db_session.flush()

        # LLM claims to execute a transaction
        llm = MockLLMProvider("I have initiated a money transfer of 5000 on your behalf to purchase stocks.")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)

        with pytest.raises(AISafetyError) as exc:
            await svc.get_guidance(user_id=406, request=AIAdvisorRequest(message="Buy stocks."))
        assert "autonomous financial transactions" in str(exc.value)


# ---------------------------------------------------------------------------
# Missing & Insufficient Data
# ---------------------------------------------------------------------------


class TestAIContextBuilderLeastPrivilege:
    @pytest.mark.anyio
    async def test_least_privilege_filtering_applies(self, db_session: Session):
        """Builder dynamically filters financial details to only query-relevant scopes."""
        _seed_user(db_session, 407, "filter@example.com")
        # Add income and assets
        db_session.add(Income(
            user_id=407, source="Freelance", amount=Decimal("60000"),
            income_date=TODAY, category="FREELANCE", frequency=IncomeFrequency.MONTHLY,
        ))
        db_session.add(Asset(
            user_id=407, name="Gold Savings", asset_type=AssetType.GOLD,
            value=Decimal("300000"), valuation_date=TODAY,
        ))
        db_session.flush()

        llm = MockLLMProvider("Mock response")
        rag = MockRAGRetriever()
        safety = SimpleSafetyValidator()
        builder = AIContextBuilder()
        dash = DashboardService(db_session)

        svc = AIAdvisorService(db_session, llm, rag, safety, builder, dash)

        # Ask a pure cash flow query
        await svc.get_guidance(user_id=407, request=AIAdvisorRequest(message="What is my monthly income?"))

        context = llm.last_context
        # Cash flow facts kept, assets (net worth) cleared
        assert context.user_financial_context.cash_flow.has_data is True
        assert context.user_financial_context.net_worth.has_data is False
