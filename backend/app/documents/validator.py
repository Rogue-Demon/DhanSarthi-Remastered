"""
Validator for extracted financial information.

Checks logical consistency (impossible values, date ranges, balance checks)
and generates descriptive warning payloads for user review.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import date
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DocumentType
from app.models.income import Income
from app.documents.financial_extractor import ExtractedField, TransactionCandidate, FinancialExtractionResult


class FinancialDocumentValidator:
    """Enforces mathematical and database verification rules on document extraction candidates."""

    def validate(self, db: Session, user_id: int, result: FinancialExtractionResult) -> List[str]:
        """
        Scan extracted metadata and transactions for internal and database conflicts.

        Returns:
            List[str]: List of warning message strings. Empty if completely consistent.
        """
        warnings = []

        # 1. Internal logical consistency checks
        self._check_salary_slip_consistency(result, warnings)
        self._check_loan_statement_consistency(result, warnings)
        self._check_transaction_consistency(result, warnings)

        # 2. Database cross-reference checks (e.g., salary slip conflicts)
        self._check_database_conflicts(db, user_id, result, warnings)

        return warnings

    def _check_salary_slip_consistency(self, result: FinancialExtractionResult, warnings: List[str]):
        if result.document_type != DocumentType.SALARY_SLIP:
            return

        gross = self._get_field_value(result, "gross_salary")
        net = self._get_field_value(result, "net_salary")
        deductions = self._get_field_value(result, "total_deductions")

        if gross is not None and gross <= Decimal("0"):
            warnings.append("Gross salary is zero or negative.")
        if net is not None and net <= Decimal("0"):
            warnings.append("Net salary is zero or negative.")
        if deductions is not None and deductions < Decimal("0"):
            warnings.append("Total deductions cannot be negative.")

        # Math verification: Gross - Deductions should equal Net
        if gross is not None and net is not None and deductions is not None:
            expected_net = gross - deductions
            if abs(expected_net - net) > Decimal("1.00"):  # Allow small rounding offset
                warnings.append(
                    f"Salary mismatch: Gross ({gross}) minus Deductions ({deductions}) "
                    f"does not equal Net ({net})."
                )

    def _check_loan_statement_consistency(self, result: FinancialExtractionResult, warnings: List[str]):
        if result.document_type != DocumentType.LOAN_STATEMENT:
            return

        principal = self._get_field_value(result, "principal_amount")
        emi = self._get_field_value(result, "emi")
        balance = self._get_field_value(result, "outstanding_balance")

        if principal is not None and principal <= Decimal("0"):
            warnings.append("Loan principal amount is zero or negative.")
        if emi is not None and emi <= Decimal("0"):
            warnings.append("Monthly EMI is zero or negative.")
        if balance is not None and balance < Decimal("0"):
            warnings.append("Outstanding balance cannot be negative.")
        if balance is not None and principal is not None and balance > principal:
            warnings.append("Outstanding balance exceeds original principal amount.")

    def _check_transaction_consistency(self, result: FinancialExtractionResult, warnings: List[str]):
        # Check transaction candidates for bank statements
        for idx, t in enumerate(result.transactions, start=1):
            # Parse candidate amounts
            deb_val = None
            cred_val = None
            try:
                if t.debit:
                    deb_val = Decimal(t.debit)
                    if deb_val <= Decimal("0"):
                        warnings.append(f"Row {idx}: Debit amount ({deb_val}) must be positive.")
            except (InvalidOperation, ValueError):
                warnings.append(f"Row {idx}: Invalid debit format.")

            try:
                if t.credit:
                    cred_val = Decimal(t.credit)
                    if cred_val <= Decimal("0"):
                        warnings.append(f"Row {idx}: Credit amount ({cred_val}) must be positive.")
            except (InvalidOperation, ValueError):
                warnings.append(f"Row {idx}: Invalid credit format.")

            if deb_val is not None and cred_val is not None:
                warnings.append(f"Row {idx}: Both Debit and Credit are populated on the same row.")

            if deb_val is None and cred_val is None:
                warnings.append(f"Row {idx}: Transaction has neither Debit nor Credit.")

    def _check_database_conflicts(
        self, db: Session, user_id: int, result: FinancialExtractionResult, warnings: List[str]
    ):
        if result.document_type == DocumentType.SALARY_SLIP:
            net_salary = self._get_field_value(result, "net_salary")
            if net_salary is not None:
                # Find latest active income for the user categorized as Salary
                stmt = (
                    select(Income)
                    .where(Income.user_id == user_id)
                    .where(Income.category.ilike("salary"))
                    .where(Income.deleted_at.is_(None))
                    .order_by(Income.income_date.desc())
                    .limit(1)
                )
                existing = db.execute(stmt).scalar_one_or_none()
                if existing:
                    # If salary differs, generate conflict warning
                    if abs(existing.amount - net_salary) > Decimal("5.00"):
                        warnings.append(
                            f"CONFLICT_DETECTED: Extracted Net Salary ({net_salary}) differs "
                            f"from your existing database salary record ({existing.amount})."
                        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_field_value(self, result: FinancialExtractionResult, name: str) -> Optional[Any]:
        for f in result.fields:
            if f.name == name:
                return f.value
        return None
