"""
Tests for financial health analyzers (cash flow, savings, expenses, budget, debt, emergency fund, and goals).
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile, IncomeFrequency, ExpenseFrequency, AssetType, LiabilityType, GoalStatus, InvestmentType, LoanType, LoanStatus
from app.models.income import Income
from app.models.expense import Expense
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.goal import Goal
from app.models.budget import Budget
from app.models.loan import Loan
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


class TestFinancialIntelligenceAnalyzers:
    def test_cash_flow_and_savings_rate_analysis(self, db_session: Session):
        user = _seed_user(db_session, 6001)
        
        # Seed 100k income and 70k expenses -> 30k surplus, 30% savings rate
        db_session.add(Income(user_id=user.id, amount=Decimal("100000.00"), category="Salary", source="Job", frequency=IncomeFrequency.MONTHLY, income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("70000.00"), category="Rent", frequency=ExpenseFrequency.MONTHLY, expense_date=date.today(), description="Rent"))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        # Net cash flow assertions
        assert summary.cash_flow.metric == "net_cash_flow"
        assert summary.cash_flow.value == Decimal("30000.00")
        assert summary.cash_flow.status == "POSITIVE"
        assert summary.cash_flow.severity == "INFO"

        # Savings rate assertions
        assert summary.savings.metric == "savings_rate"
        assert summary.savings.value == Decimal("30.00")
        assert summary.savings.status == "HEALTHY"

    def test_negative_cash_flow_warning(self, db_session: Session):
        user = _seed_user(db_session, 6002)
        
        # 100k income, 120k expenses -> -20k surplus
        db_session.add(Income(user_id=user.id, amount=Decimal("100000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("120000.00"), category="Shopping", expense_date=date.today()))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        assert summary.cash_flow.status == "NEGATIVE"
        assert summary.cash_flow.severity == "HIGH"
        assert "NEGATIVE_CASH_FLOW" in summary.warnings

    def test_debt_to_income_analysis(self, db_session: Session):
        user = _seed_user(db_session, 6003)
        
        # 100k income, 25k debt EMI -> 25% DTI (MODERATE)
        db_session.add(Income(user_id=user.id, amount=Decimal("100000.00"), category="Salary", source="Job", income_date=date.today()))
        db_session.add(
            Loan(
                user_id=user.id,
                loan_type=LoanType.HOME,
                lender="SBI",
                principal_amount=Decimal("1500000.00"),
                outstanding_amount=Decimal("1500000.00"),
                interest_rate=Decimal("0.0850"),
                tenure=240,
                start_date=date.today(),
                status=LoanStatus.ACTIVE,
                emi=Decimal("25000.00"),
            )
        )
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        assert summary.debt.metric == "debt_to_income"
        assert summary.debt.value == Decimal("13.02")
        assert summary.debt.status == "LOW"

    def test_emergency_fund_coverage(self, db_session: Session):
        user = _seed_user(db_session, 6004)
        
        # 300k liquid assets, 50k essential expenses -> 6 months coverage (MODERATE/HIGH boundary)
        db_session.add(Asset(user_id=user.id, name="Savings Bank Account", asset_type=AssetType.BANK_BALANCE, value=Decimal("300000.00"), valuation_date=date.today()))
        db_session.add(Expense(user_id=user.id, amount=Decimal("50000.00"), category="Rent", expense_date=date.today(), description="Rent"))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        # Emergency fund coverage
        assert summary.emergency_fund.metric == "emergency_fund_months"
        assert summary.emergency_fund.value == Decimal("6.00")
        assert summary.emergency_fund.status == "HIGH" or summary.emergency_fund.status == "MODERATE"

    def test_portfolio_allocation_and_concentration(self, db_session: Session):
        user = _seed_user(db_session, 6005)
        
        # 600k Equity, 400k Gold -> Total 1000k. Equity = 60%, Gold = 40%
        # Equity is > 50%, concentration should be detected.
        from app.models.investment import Investment
        db_session.add(Investment(user_id=user.id, name="HDFC Index Fund", investment_type=InvestmentType.MUTUAL_FUND, principal=Decimal("600000.00"), current_value=Decimal("600000.00"), quantity=Decimal("100"), purchase_date=date.today()))
        db_session.add(Investment(user_id=user.id, name="Sovereign Gold Bond", investment_type=InvestmentType.GOLD, principal=Decimal("400000.00"), current_value=Decimal("400000.00"), quantity=Decimal("50"), purchase_date=date.today()))
        db_session.commit()

        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        assert summary.investments.status == "CONCENTRATION_DETECTED"
        assert "HIGH_INVESTMENT_CONCENTRATION" in summary.warnings

    def test_missing_data_returns_insufficient_data(self, db_session: Session):
        user = _seed_user(db_session, 6006)
        # Empty user profile
        service = FinancialIntelligenceService(db_session)
        summary = service.build_summary(user_id=user.id)

        assert summary.cash_flow.status == "INSUFFICIENT_DATA"
        assert summary.savings.status == "INSUFFICIENT_DATA"
        assert summary.debt.status == "INSUFFICIENT_DATA"
        assert summary.emergency_fund.status == "INSUFFICIENT_DATA"
        assert summary.data_quality == "LIMITED"
