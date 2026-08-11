"""
Tests for user confirmation, selective field imports, duplicate import prevention,
and atomic commit transaction safety.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DocumentStatus, DocumentType, Persona, RiskProfile, TransactionType
from app.models.user import User
from app.models.profile import Profile
from app.models.financial_document import FinancialDocument, DocumentExtraction
from app.models.income import Income
from app.models.transaction import Transaction
from app.services.document_service import DocumentService
from app.services.document_import_service import FinancialDocumentImportService
from app.schemas.document import ConfirmationRequest
from app.documents.exceptions import ConfirmationInvalidError


def _seed_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"confirm_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"Confirm User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


def _create_mock_extraction(
    db: Session, doc_id: int, doc_type: DocumentType, fields: list, txs: list
) -> DocumentExtraction:
    ext = DocumentExtraction(
        document_id=doc_id,
        document_type=doc_type,
        extraction_version="1.0.0",
        classification_confidence=0.95,
        extracted_fields=fields,
        extracted_transactions=txs,
        warnings=[],
        raw_page_count=1,
    )
    db.add(ext)
    db.commit()
    return ext


class TestDocumentConfirmationImport:
    @pytest.mark.anyio
    async def test_confirm_and_import_salary_slip_fields(self, db_session: Session):
        _seed_user(db_session, 4001)
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        doc = await doc_svc.upload_document(
            user_id=4001,
            filename="payslip.txt",
            content_type="text/plain",
            data=b"net salary Rs 85000",
        )
        
        # Manually force processed state and seed extraction results
        doc.status = DocumentStatus.EXTRACTED
        doc.document_type = DocumentType.SALARY_SLIP
        db_session.commit()

        fields_cand = [
            {"name": "net_salary", "value": "85000.00", "confidence": 0.98, "source_page": 1, "source_text_ref": ""}
        ]
        _create_mock_extraction(db_session, doc.id, DocumentType.SALARY_SLIP, fields_cand, [])

        req = ConfirmationRequest(confirmed_fields=["net_salary"], confirmed_transactions=[])
        res = import_svc.confirm_and_import(document_id=doc.id, user_id=4001, req=req)

        assert res.imported_fields_count == 1
        assert res.status == DocumentStatus.CONFIRMED

        # Verify Income record was created
        stmt = select(Income).where(Income.user_id == 4001)
        incomes = db_session.execute(stmt).scalars().all()
        assert len(incomes) == 1
        assert incomes[0].amount == Decimal("85000.00")
        assert incomes[0].category == "Salary"

    @pytest.mark.anyio
    async def test_confirm_and_import_bank_transactions(self, db_session: Session):
        _seed_user(db_session, 4002)
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        doc = await doc_svc.upload_document(
            user_id=4002,
            filename="statement.csv",
            content_type="text/csv",
            data=b"date,desc,amount\n12-08-2026,Rent,-15000",
        )
        doc.status = DocumentStatus.EXTRACTED
        doc.document_type = DocumentType.BANK_STATEMENT
        db_session.commit()

        txs_cand = [
            {
                "candidate_id": "tx_cand_1",
                "date": "2026-08-12",
                "description": "Rent Payment",
                "debit": "15000.00",
                "credit": None,
                "balance": "35000.00",
                "currency": "INR"
            }
        ]
        _create_mock_extraction(db_session, doc.id, DocumentType.BANK_STATEMENT, [], txs_cand)

        req = ConfirmationRequest(confirmed_fields=[], confirmed_transactions=["tx_cand_1"])
        res = import_svc.confirm_and_import(document_id=doc.id, user_id=4002, req=req)

        assert res.imported_transactions_count == 1
        assert res.status == DocumentStatus.CONFIRMED

        # Verify Transaction record was created
        stmt = select(Transaction).where(Transaction.user_id == 4002)
        txs = db_session.execute(stmt).scalars().all()
        assert len(txs) == 1
        assert txs[0].amount == Decimal("15000.00")
        assert txs[0].transaction_type == TransactionType.EXPENSE
        assert txs[0].description == "Rent Payment"

    @pytest.mark.anyio
    async def test_double_import_protection(self, db_session: Session):
        _seed_user(db_session, 4003)
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        doc = await doc_svc.upload_document(
            user_id=4003,
            filename="payslip.txt",
            content_type="text/plain",
            data=b"net salary Rs 85000",
        )
        doc.status = DocumentStatus.EXTRACTED
        doc.document_type = DocumentType.SALARY_SLIP
        db_session.commit()

        fields_cand = [
            {"name": "net_salary", "value": "85000.00", "confidence": 0.98, "source_page": 1, "source_text_ref": ""}
        ]
        _create_mock_extraction(db_session, doc.id, DocumentType.SALARY_SLIP, fields_cand, [])

        req = ConfirmationRequest(confirmed_fields=["net_salary"], confirmed_transactions=[])
        
        # First confirmation
        res1 = import_svc.confirm_and_import(document_id=doc.id, user_id=4003, req=req)
        assert res1.imported_fields_count == 1

        # Reset state to allow second import attempt on same document
        doc.status = DocumentStatus.EXTRACTED
        db_session.commit()

        # Second confirmation (should be skipped and warned)
        res2 = import_svc.confirm_and_import(document_id=doc.id, user_id=4003, req=req)
        assert res2.imported_fields_count == 0
        assert len(res2.warnings) > 0
        assert "already exists" in res2.warnings[0]

    @pytest.mark.anyio
    async def test_confirm_invalid_state_raises_error(self, db_session: Session):
        _seed_user(db_session, 4004)
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        doc = await doc_svc.upload_document(
            user_id=4004,
            filename="statement.pdf",
            content_type="application/pdf",
            data=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj",
        )
        # Document is in UPLOADED state, not EXTRACTED/REVIEW_REQUIRED
        req = ConfirmationRequest(confirmed_fields=[], confirmed_transactions=[])
        with pytest.raises(ConfirmationInvalidError):
            import_svc.confirm_and_import(document_id=doc.id, user_id=4004, req=req)

    @pytest.mark.anyio
    async def test_import_atomic_rollback_on_failure(self, db_session: Session):
        _seed_user(db_session, 4005)
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        doc = await doc_svc.upload_document(
            user_id=4005,
            filename="statement.csv",
            content_type="text/csv",
            data=b"date,desc,amount\n12-08-2026,Rent,-15000",
        )
        doc.status = DocumentStatus.EXTRACTED
        doc.document_type = DocumentType.BANK_STATEMENT
        db_session.commit()

        txs_cand = [
            {
                "candidate_id": "tx_cand_good",
                "date": "2026-08-12",
                "description": "Good Tx",
                "debit": "500.00",
                "currency": "INR"
            },
            {
                "candidate_id": "tx_cand_bad",
                "date": "invalid-date-string",  # Force ValueError
                "description": "Bad Tx",
                "debit": "500.00",
                "currency": "INR"
            }
        ]
        _create_mock_extraction(db_session, doc.id, DocumentType.BANK_STATEMENT, [], txs_cand)

        req = ConfirmationRequest(
            confirmed_fields=[],
            confirmed_transactions=["tx_cand_good", "tx_cand_bad"]
        )

        with pytest.raises(ConfirmationInvalidError):
            import_svc.confirm_and_import(document_id=doc.id, user_id=4005, req=req)

        # Verify nothing was imported (atomicity check)
        stmt = select(Transaction).where(Transaction.user_id == 4005)
        txs = db_session.execute(stmt).scalars().all()
        assert len(txs) == 0
        # Parent document status is not changed to CONFIRMED
        assert doc.status == DocumentStatus.EXTRACTED
