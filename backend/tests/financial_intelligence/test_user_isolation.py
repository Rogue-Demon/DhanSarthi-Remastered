"""
Tests to verify IDOR protection and user data isolation in the Decision Engine.
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
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.financial_intelligence.exceptions import FinancialIntelligenceAccessDeniedError


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


class TestFinancialIntelligenceUserIsolation:
    def test_user_a_cannot_view_user_b_financial_summary(self, db_session: Session):
        user_a = _seed_user(db_session, 9001)
        user_b = _seed_user(db_session, 9002)

        # Seed data only for User B
        db_session.add(Income(user_id=user_b.id, amount=Decimal("150000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user_b.id, amount=Decimal("50000.00"), category="Rent", expense_date=date.today()))
        
        # User A has no data
        db_session.commit()

        service = FinancialIntelligenceService(db_session)

        # Retrieve summary as User A -> Should return empty/insufficient data, not User B's metrics
        summary_a = service.build_summary(user_id=user_a.id)
        assert summary_a.cash_flow.value == Decimal("0")
        assert summary_a.cash_flow.status == "INSUFFICIENT_DATA"

        # Retrieve summary as User B -> Should return correct metrics
        summary_b = service.build_summary(user_id=user_b.id)
        assert summary_b.cash_flow.value == Decimal("100000.00")
        assert summary_b.cash_flow.status == "POSITIVE"

    def test_run_goal_scenario_verifies_goal_ownership(self, db_session: Session):
        user_a = _seed_user(db_session, 9003)
        user_b = _seed_user(db_session, 9004)

        from app.models.goal import Goal
        # Goal owned by User B
        goal_b = Goal(user_id=user_b.id, name="House Downpayment", target_amount=Decimal("500000.00"), current_amount=Decimal("50000.00"), status="ACTIVE")
        db_session.add(goal_b)
        db_session.commit()

        service = FinancialIntelligenceService(db_session)

        # User A attempts to simulate goal contribution scenario for User B's goal -> Raises UnauthorizedError
        with pytest.raises(FinancialIntelligenceAccessDeniedError):
            service.run_goal_scenario(
                user_id=user_a.id,
                goal_id=goal_b.id,
                proposed_monthly_contribution=Decimal("10000.00"),
            )
