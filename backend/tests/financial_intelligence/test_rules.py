"""
Tests for centralized warnings and opportunity rules.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile, IncomeFrequency, ExpenseFrequency, AssetType, LiabilityType, BudgetPeriod
from app.models.income import Income
from app.models.expense import Expense
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.budget import Budget
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


class TestFinancialIntelligenceRules:
    def test_evaluate_warnings_and_opportunities(self, db_session: Session):
        user = _seed_user(db_session, 8001)

        # Income: 100,000, Expenses: 40,000 (Rent: 30,000 -> essential, Shopping: 10,000)
        # Liquid assets: 500,000 -> emergency fund = 500,000 / 30,000 = 16.6 months (EXCESS_CASH_RESERVE)
        # Budget: total 50,000, spending 40,000 -> utilization 80% (ON_TRACK)
        # Surplus: 60,000 -> POSITIVE_MONTHLY_SURPLUS
        db_session.add(Income(user_id=user.id, amount=Decimal("100000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("30000.00"), category="Rent", expense_date=date.today(), description="Rent"))
        db_session.add(Expense(user_id=user.id, amount=Decimal("10000.00"), category="Shopping", expense_date=date.today()))
        db_session.add(Asset(user_id=user.id, name="Savings", asset_type=AssetType.BANK_BALANCE, value=Decimal("500000.00"), valuation_date=date.today()))
        db_session.add(Budget(user_id=user.id, category="Rent", amount=Decimal("30000.00"), period=BudgetPeriod.MONTHLY, start_date=date.today()))
        db_session.add(Budget(user_id=user.id, category="Shopping", amount=Decimal("20000.00"), period=BudgetPeriod.MONTHLY, start_date=date.today()))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        assert not summary.warnings  # No warnings since cash flow is positive, emergency coverage is good
        assert "POSITIVE_MONTHLY_SURPLUS" in summary.opportunities
        assert "EXCESS_CASH_RESERVE" in summary.opportunities
        assert "UNUSED_BUDGET_CAPACITY" not in summary.opportunities  # 40k / 50k = 80% (not < 70%)
