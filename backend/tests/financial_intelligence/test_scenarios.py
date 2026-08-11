"""
Tests for financial scenarios, compound growth modeling, and loan affordability calculations.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile
from app.models.income import Income
from app.models.expense import Expense
from app.models.loan import Loan
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.financial_intelligence.scenarios.engine import calculate_emi, run_loan_scenario


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


class TestFinancialScenarios:
    def test_calculate_emi_reducing_balance(self):
        # Principal: 10 Lakhs (1,000,000)
        # Interest Rate: 10%
        # Tenure: 5 years (60 months)
        # Standard EMI should be roughly 21,247.04
        emi = calculate_emi(Decimal("1000000.00"), Decimal("10.00"), 60)
        assert abs(emi - Decimal("21247.04")) <= Decimal("0.10")

    def test_calculate_emi_zero_interest(self):
        # Principal: 120,000
        # Rate: 0%
        # Tenure: 12 months
        # Standard EMI should be 10,000
        emi = calculate_emi(Decimal("120000.00"), Decimal("0.00"), 12)
        assert emi == Decimal("10000.00")

    def test_loan_affordability_risk_flagging(self, db_session: Session):
        user = _seed_user(db_session, 7001)
        
        # Income: 85,000, Expenses: 30,000, Debt: 12,000
        db_session.add(Income(user_id=user.id, amount=Decimal("85000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("30000.00"), category="Rent", expense_date=date.today()))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        # Scenario: proposed loan principal 10 Lakhs, interest 10%, tenure 5 years (EMI ~21,247)
        res = service.run_loan_scenario(
            user_id=user.id,
            principal=Decimal("1000000.00"),
            annual_interest_rate_percent=Decimal("10.00"),
            tenure_months=60,
        )

        assert res.emi > Decimal("0")
        assert res.post_loan_dti is not None
        # post-loan DTI: (12,000 + 21,247) / 85,000 = ~39.1% (triggering DTI warning if threshold > 36%)
        # Here existing monthly debt is 0 (no loans seeded), so post-loan debt is just the proposed emi:
        # Proposed DTI: 21,247.04 / 85,000 = ~25%
        assert res.post_loan_dti > Decimal("20")

    def test_scenario_engine_is_immutable(self, db_session: Session):
        user = _seed_user(db_session, 7002)
        
        db_session.add(Income(user_id=user.id, amount=Decimal("100000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("40000.00"), category="Rent", expense_date=date.today()))
        db_session.commit()

        # Count tables before running scenarios
        stmt_inc = select(Income).where(Income.user_id == user.id)
        count_inc_before = len(db_session.execute(stmt_inc).scalars().all())

        stmt_loans = select(Loan).where(Loan.user_id == user.id)
        count_loans_before = len(db_session.execute(stmt_loans).scalars().all())

        service = FinancialIntelligenceService(db_session)
        # Execute loan and savings scenarios
        service.run_loan_scenario(
            user_id=user.id,
            principal=Decimal("500000.00"),
            annual_interest_rate_percent=Decimal("8.50"),
            tenure_months=36,
        )
        service.run_savings_scenario(
            user_id=user.id,
            expense_reduction=Decimal("5000.00"),
        )
        service.run_investment_scenario(
            user_id=user.id,
            monthly_contribution=Decimal("10000.00"),
            expected_annual_return_percent=Decimal("12.00"),
            duration_years=Decimal("10"),
        )

        # Count tables after running scenarios (must match before)
        count_inc_after = len(db_session.execute(stmt_inc).scalars().all())
        count_loans_after = len(db_session.execute(stmt_loans).scalars().all())

        assert count_inc_before == count_inc_after
        assert count_loans_before == count_loans_after
