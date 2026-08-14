"""
Document Import Service for selective confirmation.

Handles importing approved metadata fields and transaction candidates into
the authoritative database using existing domain services.
Enforces double-import prevention, date checks, and transaction safety boundaries.
"""

from __future__ import annotations

import datetime
import re
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DocumentStatus, DocumentType, IncomeFrequency, TransactionType, AssetType, LiabilityType
from app.models.income import Income
from app.models.expense import Expense
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.services.income_service import IncomeService
from app.services.expense_service import ExpenseService
from app.services.asset_service import AssetService
from app.services.liability_service import LiabilityService
from app.services.transaction_service import TransactionService
from app.services.document_service import DocumentService
from app.documents.exceptions import ConfirmationInvalidError, ImportFailedError
from app.schemas.document import (
    ConfirmationRequest,
    ConfirmationResponse,
    IncomeCandidateSchema,
    ExpenseCandidateSchema,
    AssetCandidateSchema,
    LiabilityCandidateSchema,
    MappedFieldExplanationSchema,
)
from app.documents.mapping_registry import default_mapping_registry, DestinationType
from app.core.exceptions import handle_db_exceptions


class FinancialDocumentImportService:
    """Orchestrates importing user-confirmed document extraction candidates into financial tables."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._doc_service = DocumentService(db)
        self._income_service = IncomeService(db)
        self._expense_service = ExpenseService(db)
        self._asset_service = AssetService(db)
        self._liability_service = LiabilityService(db)
        self._transaction_service = TransactionService(db)

    @staticmethod
    def _parse_salary_period_date(period_str: Any) -> Optional[datetime.date]:
        if not period_str:
            return None
        period_str = str(period_str).strip()
        m_iso = re.search(r"\b(\d{4})[-/.](\d{1,2})\b", period_str)
        if m_iso:
            yr, mo = int(m_iso.group(1)), int(m_iso.group(2))
            if 1 <= mo <= 12:
                return datetime.date(yr, mo, 1)
        m_text = re.search(
            r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*,?\s*(\d{4})\b",
            period_str,
            re.IGNORECASE,
        )
        if m_text:
            month_str, yr_str = m_text.group(1).lower(), m_text.group(2)
            month_names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            for idx, m_prefix in enumerate(month_names, 1):
                if month_str.startswith(m_prefix):
                    return datetime.date(int(yr_str), idx, 1)
        return None

    def confirm_and_import(
        self,
        document_id: int,
        user_id: int,
        req: ConfirmationRequest,
    ) -> ConfirmationResponse:
        """
        Import selected Income, Expense, Asset, Liability, Metadata, and Transaction candidates.
        """
        doc = self._doc_service.get_document(document_id, user_id)
        if doc.status not in (DocumentStatus.EXTRACTED, DocumentStatus.REVIEW_REQUIRED):
            raise ConfirmationInvalidError(
                f"Document must be in EXTRACTED or REVIEW_REQUIRED state. Current: {doc.status}"
            )

        extraction = self._doc_service.get_extraction(document_id, user_id)
        
        imported_income_count = 0
        imported_expense_count = 0
        imported_asset_count = 0
        imported_liability_count = 0
        imported_metadata_count = 0
        imported_txs_count = 0

        warnings = []
        field_explanations: List[MappedFieldExplanationSchema] = []

        original_commit = self._db.commit
        self._db.commit = lambda: None

        try:
            with handle_db_exceptions(resource="FinancialDocumentImport"):
                fields_map = {f["name"]: f for f in (extraction.extracted_fields or [])}
                txs_map = {t["candidate_id"]: t for t in (extraction.extracted_transactions or [])}

                # 1. Process Income Candidates
                for inc_item in req.confirmed_income:
                    inc_amt = Decimal(str(inc_item.amount))
                    inc_date = inc_item.income_date or datetime.date.today()
                    inc_source = inc_item.source or "Document Import"

                    stmt = (
                        select(Income)
                        .where(Income.user_id == user_id)
                        .where(Income.amount == inc_amt)
                        .where(Income.income_date == inc_date)
                        .where(Income.source == inc_source)
                        .where(Income.deleted_at.is_(None))
                    )
                    exists = self._db.execute(stmt).scalar_one_or_none()
                    if exists:
                        warnings.append(f"Income record (₹{inc_amt:,.2f}) on {inc_date} from {inc_source} already exists. Skipped duplicate.")
                        continue

                    self._income_service.create_income(
                        user_id=user_id,
                        source=inc_source,
                        amount=inc_amt,
                        income_date=inc_date,
                        category=inc_item.category or "Salary",
                        currency=inc_item.currency or "INR",
                        frequency=IncomeFrequency.MONTHLY,
                        description=inc_item.description or f"Imported from {doc.original_filename}"
                    )
                    imported_income_count += 1

                # 2. Process Expense Candidates
                for exp_item in req.confirmed_expenses:
                    exp_amt = Decimal(str(exp_item.amount))
                    exp_date = exp_item.expense_date or datetime.date.today()
                    exp_merchant = exp_item.merchant or "Vendor"

                    stmt = (
                        select(Expense)
                        .where(Expense.user_id == user_id)
                        .where(Expense.amount == exp_amt)
                        .where(Expense.expense_date == exp_date)
                        .where(Expense.category == (exp_item.category or "Utilities"))
                        .where(Expense.deleted_at.is_(None))
                    )
                    exists = self._db.execute(stmt).scalar_one_or_none()
                    if exists:
                        warnings.append(f"Expense record (₹{exp_amt:,.2f}) on {exp_date} already exists. Skipped duplicate.")
                        continue

                    self._expense_service.create_expense(
                        user_id=user_id,
                        category=exp_item.category or "Utilities",
                        amount=exp_amt,
                        expense_date=exp_date,
                        currency=exp_item.currency or "INR",
                        description=f"{exp_merchant} - {exp_item.description or doc.original_filename}"
                    )
                    imported_expense_count += 1

                # 3. Process Asset Candidates
                for asset_item in req.confirmed_assets:
                    asset_val = Decimal(str(asset_item.value))
                    asset_name = asset_item.name or "Holding"
                    
                    try:
                        a_type = AssetType(asset_item.asset_type)
                    except ValueError:
                        a_type = AssetType.BANK_BALANCE

                    stmt = (
                        select(Asset)
                        .where(Asset.user_id == user_id)
                        .where(Asset.name == asset_name)
                        .where(Asset.value == asset_val)
                    )
                    exists = self._db.execute(stmt).scalar_one_or_none()
                    if exists:
                        warnings.append(f"Asset '{asset_name}' (₹{asset_val:,.2f}) already exists. Skipped duplicate.")
                        continue

                    self._asset_service.create_asset(
                        user_id=user_id,
                        asset_type=a_type,
                        name=asset_name,
                        value=asset_val,
                        currency="INR",
                        valuation_date=asset_item.maturity_date or datetime.date.today(),
                        asset_metadata={"institution": asset_item.institution, "description": asset_item.description}
                    )
                    imported_asset_count += 1

                # 4. Process Liability Candidates
                for liab_item in req.confirmed_liabilities:
                    liab_amt = Decimal(str(liab_item.amount))
                    liab_name = liab_item.name or "Debt"
                    
                    try:
                        l_type = LiabilityType(liab_item.liability_type)
                    except ValueError:
                        l_type = LiabilityType.PERSONAL_DEBT

                    stmt = (
                        select(Liability)
                        .where(Liability.user_id == user_id)
                        .where(Liability.name == liab_name)
                        .where(Liability.outstanding_amount == liab_amt)
                    )
                    exists = self._db.execute(stmt).scalar_one_or_none()
                    if exists:
                        warnings.append(f"Liability '{liab_name}' (₹{liab_amt:,.2f}) already exists. Skipped duplicate.")
                        continue

                    self._liability_service.create_liability(
                        user_id=user_id,
                        liability_type=l_type,
                        name=liab_name,
                        outstanding_amount=liab_amt,
                        currency="INR",
                        interest_rate=liab_item.interest_rate,
                        liability_metadata={"institution": liab_item.institution, "monthly_payment": str(liab_item.monthly_payment) if liab_item.monthly_payment else None}
                    )
                    imported_liability_count += 1

                # 5. Process confirmed metadata fields (Backward Compatibility & Metadata Logging)
                salary_date = extraction.period_end or datetime.date.today()
                if "salary_period" in fields_map:
                    p_date = self._parse_salary_period_date(fields_map["salary_period"].get("value"))
                    if p_date:
                        salary_date = p_date

                employer_name = fields_map.get("employer", {}).get("value")
                source_name = f"Salary ({employer_name})" if employer_name else "Salary Slip Import"

                for field_name in req.confirmed_fields:
                    candidate = fields_map.get(field_name)
                    if not candidate:
                        continue
                    val_str = candidate.get("value")

                    if doc.document_type == DocumentType.SALARY_SLIP:
                        if field_name == "net_salary" and imported_income_count == 0:
                            salary_val = Decimal(str(val_str))
                            stmt = (
                                select(Income)
                                .where(Income.user_id == user_id)
                                .where(Income.amount == salary_val)
                                .where(Income.income_date == salary_date)
                                .where(Income.source == source_name)
                                .where(Income.deleted_at.is_(None))
                            )
                            exists = self._db.execute(stmt).scalar_one_or_none()
                            if not exists:
                                self._income_service.create_income(
                                    user_id=user_id,
                                    source=source_name,
                                    amount=salary_val,
                                    income_date=salary_date,
                                    category="Salary",
                                    currency="INR",
                                    frequency=IncomeFrequency.MONTHLY,
                                    description=f"Imported Net Salary from {doc.original_filename}"
                                )
                                imported_income_count += 1
                            else:
                                warnings.append(f"Income record (₹{salary_val:,.2f}) on {salary_date} from {source_name} already exists. Skipped duplicate.")
                        elif field_name == "gross_salary":
                            gross_val = Decimal(str(val_str))
                            warnings.append(f"Gross salary (₹{gross_val:,.2f}) recorded as metadata; cash inflow created via Net Salary.")
                            imported_metadata_count += 1
                        elif field_name == "total_deductions":
                            ded_val = Decimal(str(val_str))
                            warnings.append(f"Total deductions (₹{ded_val:,.2f}) recorded as metadata; not auto-created as expense.")
                            imported_metadata_count += 1
                        else:
                            imported_metadata_count += 1
                    else:
                        imported_metadata_count += 1

                # 6. Process Transactions
                for candidate_id in req.confirmed_transactions:
                    candidate = txs_map.get(candidate_id)
                    if not candidate:
                        continue
                    try:
                        t_date = datetime.date.fromisoformat(candidate["date"])
                    except (ValueError, TypeError):
                        raise ConfirmationInvalidError(f"Invalid date format on transaction candidate: {candidate.get('date')}")

                    debit_str = candidate.get("debit")
                    credit_str = candidate.get("credit")
                    
                    if credit_str:
                        t_type = TransactionType.INCOME
                        t_amount = Decimal(credit_str)
                    elif debit_str:
                        t_type = TransactionType.EXPENSE
                        t_amount = Decimal(debit_str)
                    else:
                        continue

                    t_desc = candidate.get("description", "Imported Transaction")
                    source_name = f"Statement Import: {doc.original_filename}"

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
                        warnings.append(f"Transaction matching description '{t_desc}' on {t_date} already exists. Skipped duplicate.")
                        continue

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
                    imported_txs_count += 1

                # 7. Generate Field Status Explanations
                for f_name, candidate in fields_map.items():
                    rule = default_mapping_registry.get_rule(doc.document_type, f_name)
                    status_val = "SUPPORTED"
                    if rule.behavior == "METADATA":
                        status_val = "METADATA"
                    elif rule.behavior == "UNSUPPORTED":
                        status_val = "UNSUPPORTED"

                    field_explanations.append(
                        MappedFieldExplanationSchema(
                            field_name=f_name,
                            status=status_val,
                            destination=rule.destination_type.value,
                            explanation=rule.explanation
                        )
                    )

                doc.status = DocumentStatus.CONFIRMED

            self._db.commit = original_commit
            self._db.commit()

        except Exception:
            self._db.commit = original_commit
            self._db.rollback()
            raise

        total_imported_records = (
            imported_income_count +
            imported_expense_count +
            imported_asset_count +
            imported_liability_count +
            imported_metadata_count +
            imported_txs_count
        )

        return ConfirmationResponse(
            imported_fields_count=total_imported_records,
            imported_transactions_count=imported_txs_count,
            imported_income_count=imported_income_count,
            imported_expense_count=imported_expense_count,
            imported_asset_count=imported_asset_count,
            imported_liability_count=imported_liability_count,
            imported_metadata_count=imported_metadata_count,
            warnings=warnings,
            field_explanations=field_explanations,
            status=doc.status
        )

