"""
Tests to verify the AI Advisor integrates correctly with the deterministic Decision Engine results.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile
from app.models.income import Income
from app.models.expense import Expense
from app.schemas.dashboard import DashboardResponse
from app.ai.schemas.advisor import AIContext, RetrievedDocument
from app.ai.context.builder import AIContextBuilder
from app.services.financial_intelligence_service import FinancialIntelligenceService


def _seed_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"user_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


class TestFinancialIntelligenceAIIntegration:
    def test_ai_advisor_prompt_contains_serialized_intelligence_summary(self, db_session: Session):
        user = _seed_user(db_session, 10001)

        # Seed data
        db_session.add(Income(user_id=user.id, amount=Decimal("120000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("40000.00"), category="Rent", expense_date=date.today()))
        db_session.commit()

        # Build financial intelligence summary
        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        # Mock DashboardResponse for context builder
        from app.services.dashboard_service import DashboardService
        dash_svc = DashboardService(db_session)
        dash = dash_svc.build_dashboard(user_id=user.id)

        # Build context
        builder = AIContextBuilder()
        ai_context = builder.build_context(
            question="What is my savings health?",
            full_context=dash,
            retrieved_docs=[],
            financial_intelligence=summary,
        )

        prompt = builder.build_prompt(ai_context)

        # Assertions: Prompt must contain the serialized intelligence summaries as ground truth
        assert "Financial Intelligence Insights" in prompt
        # Savings rate is (120,000 - 40,000)/120,000 = 66.67% -> status is HEALTHY
        assert "HEALTHY" in prompt
        # Income amount in summary
        assert "120000" in prompt
