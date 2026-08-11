"""
Tests for logical consistency and database conflict checks (salary mismatches).
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.enums import DocumentType, Persona, RiskProfile, IncomeFrequency
from app.models.user import User
from app.models.profile import Profile
from app.models.income import Income
from app.documents.validator import FinancialDocumentValidator
from app.documents.financial_extractor import ExtractedField, TransactionCandidate, FinancialExtractionResult


def _seed_user_and_salary(db: Session, user_id: int, salary_amt: Decimal) -> User:
    u = User(id=user_id, email=f"val_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"Val User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    # Add active income record of category Salary
    db.add(
        Income(
            user_id=user_id,
            source="Employer Corp",
            amount=salary_amt,
            income_date=datetime.date(2026, 7, 31),
            category="Salary",
            currency="INR",
            frequency=IncomeFrequency.MONTHLY,
        )
    )
    db.flush()
    return u


class TestDocumentValidation:
    def test_salary_slip_mathematical_consistency(self, db_session: Session):
        validator = FinancialDocumentValidator()

        # Gross = 1,00,000, Net = 85,000, Deductions = 15,000 → Valid
        res = FinancialExtractionResult(
            document_type=DocumentType.SALARY_SLIP,
            fields=[
                ExtractedField(name="gross_salary", value=Decimal("100000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="net_salary", value=Decimal("85000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="total_deductions", value=Decimal("15000.00"), confidence=1.0, source_page=1, source_text_ref=""),
            ]
        )
        warnings = validator.validate(db_session, 999, res)
        assert len(warnings) == 0

        # Mismatch: Gross - Deductions != Net
        res_mismatch = FinancialExtractionResult(
            document_type=DocumentType.SALARY_SLIP,
            fields=[
                ExtractedField(name="gross_salary", value=Decimal("100000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="net_salary", value=Decimal("80000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="total_deductions", value=Decimal("15000.00"), confidence=1.0, source_page=1, source_text_ref=""),
            ]
        )
        warnings = validator.validate(db_session, 999, res_mismatch)
        assert len(warnings) > 0
        assert "Salary mismatch" in warnings[0]

    def test_loan_statement_logical_consistency(self, db_session: Session):
        validator = FinancialDocumentValidator()

        # Balance > Principal → Invalid
        res = FinancialExtractionResult(
            document_type=DocumentType.LOAN_STATEMENT,
            fields=[
                ExtractedField(name="principal_amount", value=Decimal("100000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="outstanding_balance", value=Decimal("120000.00"), confidence=1.0, source_page=1, source_text_ref=""),
            ]
        )
        warnings = validator.validate(db_session, 999, res)
        assert any("Outstanding balance exceeds" in w for w in warnings)

    def test_transaction_double_amount_warning(self, db_session: Session):
        validator = FinancialDocumentValidator()

        res = FinancialExtractionResult(
            document_type=DocumentType.BANK_STATEMENT,
            transactions=[
                TransactionCandidate(
                    date="2026-08-12",
                    description="ATM Cash Withdrawal",
                    debit="2000.00",
                    credit="2000.00",  # Both populated!
                    balance="13000.00"
                )
            ]
        )
        warnings = validator.validate(db_session, 999, res)
        assert any("Both Debit and Credit are populated" in w for w in warnings)

    def test_database_salary_slip_conflict_warning(self, db_session: Session):
        _seed_user_and_salary(db_session, 3001, Decimal("80000.00"))
        validator = FinancialDocumentValidator()

        # Extracted net_salary is 90,000 (differs from DB 80,000)
        res = FinancialExtractionResult(
            document_type=DocumentType.SALARY_SLIP,
            fields=[
                ExtractedField(name="gross_salary", value=Decimal("105000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="net_salary", value=Decimal("90000.00"), confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="total_deductions", value=Decimal("15000.00"), confidence=1.0, source_page=1, source_text_ref=""),
            ]
        )

        warnings = validator.validate(db_session, 3001, res)
        assert any("CONFLICT_DETECTED" in w for w in warnings)
        assert "90000" in [w for w in warnings if "CONFLICT_DETECTED" in w][0]
        assert "80000" in [w for w in warnings if "CONFLICT_DETECTED" in w][0]
