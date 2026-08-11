"""
Document Import Service for selective confirmation.

Handles importing approved metadata fields and transaction candidates into
the authoritative database using existing domain services.
Enforces double-import prevention, date checks, and transaction safety boundaries.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DocumentStatus, DocumentType, IncomeFrequency, TransactionType
from app.models.income import Income
from app.models.transaction import Transaction
from app.services.income_service import IncomeService
from app.services.transaction_service import TransactionService
from app.services.document_service import DocumentService
from app.documents.exceptions import ConfirmationInvalidError, ImportFailedError
from app.schemas.document import ConfirmationRequest, ConfirmationResponse
from app.core.exceptions import handle_db_exceptions


class FinancialDocumentImportService:
    """Orchestrates importing user-confirmed document extraction candidates into financial tables."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._doc_service = DocumentService(db)
        self._income_service = IncomeService(db)
        self._transaction_service = TransactionService(db)

    def confirm_and_import(
        self,
        document_id: int,
        user_id: int,
        req: ConfirmationRequest,
    ) -> ConfirmationResponse:
        """
        Import selected fields and transactions.

        Ensures:
          - Document belongs to user.
          - Only unprocessed fields are processed.
          - Duplicate imports are rejected.
          - Atomic database transaction boundary.
        """
        # 1. Ownership & state verification
        doc = self._doc_service.get_document(document_id, user_id)
        if doc.status not in (DocumentStatus.EXTRACTED, DocumentStatus.REVIEW_REQUIRED):
            raise ConfirmationInvalidError(
                f"Document must be in EXTRACTED or REVIEW_REQUIRED state. Current: {doc.status}"
            )

        extraction = self._doc_service.get_extraction(document_id, user_id)
        
        imported_fields = 0
        imported_txs = 0
        warnings = []

        # Temporarily redirect commit to a no-op to allow atomic outer transaction control.
        # This prevents the nested call to self._db.commit() inside the services from committing early.
        original_commit = self._db.commit
        self._db.commit = lambda: None

        try:
            # Start atomic transaction block
            with handle_db_exceptions(resource="FinancialDocumentImport"):
                # Map extraction candidate JSON representations
                fields_map = {f["name"]: f for f in (extraction.extracted_fields or [])}
                txs_map = {t["candidate_id"]: t for t in (extraction.extracted_transactions or [])}

                # 2. Process confirmed metadata fields (e.g. net_salary from salary slip)
                for field_name in req.confirmed_fields:
                    candidate = fields_map.get(field_name)
                    if not candidate:
                        raise ConfirmationInvalidError(f"Field '{field_name}' not found in extraction candidates.")
                    
                    # Import net_salary → Income
                    if field_name == "net_salary" and doc.document_type == DocumentType.SALARY_SLIP:
                        salary_val = Decimal(str(candidate["value"]))
                        
                        # Deduce date
                        salary_date = extraction.period_end or datetime.date.today()
                        source_name = "Salary Slip Import"
                        
                        # Duplicate detection
                        stmt = (
                            select(Income)
                            .where(Income.user_id == user_id)
                            .where(Income.amount == salary_val)
                            .where(Income.income_date == salary_date)
                            .where(Income.source == source_name)
                            .where(Income.deleted_at.is_(None))
                        )
                        exists = self._db.execute(stmt).scalar_one_or_none()
                        if exists:
                            warnings.append(f"Salary income record on {salary_date} already exists. Skipped field import.")
                            continue
                        
                        # Create income (will not commit due to our no-op mock)
                        self._income_service.create_income(
                            user_id=user_id,
                            source=source_name,
                            amount=salary_val,
                            income_date=salary_date,
                            category="Salary",
                            currency=candidate.get("currency", "INR"),
                            frequency=IncomeFrequency.MONTHLY,
                            description=f"Imported from {doc.original_filename}"
                        )
                        imported_fields += 1
                    else:
                        warnings.append(f"Field '{field_name}' is not currently configured for auto-import.")

                # 3. Process confirmed transactions
                for candidate_id in req.confirmed_transactions:
                    candidate = txs_map.get(candidate_id)
                    if not candidate:
                        raise ConfirmationInvalidError(f"Transaction candidate '{candidate_id}' not found.")
                    
                    # Parse date
                    try:
                        t_date = datetime.date.fromisoformat(candidate["date"])
                    except ValueError:
                        raise ConfirmationInvalidError(f"Invalid date format on transaction candidate: {candidate['date']}")

                    # Determine direction (Income vs Expense)
                    debit_str = candidate.get("debit")
                    credit_str = candidate.get("credit")
                    
                    if credit_str:
                        t_type = TransactionType.INCOME
                        t_amount = Decimal(credit_str)
                    elif debit_str:
                        t_type = TransactionType.EXPENSE
                        t_amount = Decimal(debit_str)
                    else:
                        warnings.append(f"Transaction candidate '{candidate_id}' has no amount. Skipped.")
                        continue

                    t_desc = candidate.get("description", "Imported Transaction")
                    source_name = f"Statement Import: {doc.original_filename}"

                    # Duplicate detection for transactions
                    stmt = (
                        select(Transaction)
                        .where(Transaction.user_id == user_id)
                        .where(Transaction.transaction_date == t_date)
                        .where(Transaction.amount == t_amount)
                        .where(Transaction.transaction_type == t_type)
                        .where(Transaction.description == t_desc)
                        .where(Transaction.deleted_at.is_(None))
                    )
                    exists = self._db.execute(stmt).scalar_one_or_none()
                    if exists:
                        warnings.append(f"Transaction matching description '{t_desc}' on {t_date} already exists. Skipped transaction import.")
                        continue

                    # Create transaction (will not commit due to our no-op mock)
                    self._transaction_service.create_transaction(
                        user_id=user_id,
                        transaction_type=t_type,
                        amount=t_amount,
                        transaction_date=t_date,
                        category="Imported",
                        currency=candidate.get("currency", "INR"),
                        description=t_desc,
                        source=source_name
                    )
                    imported_txs += 1

                # 4. Mark document confirmed
                doc.status = DocumentStatus.CONFIRMED

            # Restore original commit and finalize all changes in a single operation
            self._db.commit = original_commit
            self._db.commit()

        except Exception:
            # Restore original commit and perform rollback in case of error
            self._db.commit = original_commit
            self._db.rollback()
            raise

        return ConfirmationResponse(
            imported_fields_count=imported_fields,
            imported_transactions_count=imported_txs,
            warnings=warnings,
            status=doc.status
        )
