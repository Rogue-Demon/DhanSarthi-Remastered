"""
Tests for user isolation and IDOR protection in the Document Intelligence layer.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile
from app.services.document_service import DocumentService
from app.services.document_import_service import FinancialDocumentImportService
from app.schemas.document import ConfirmationRequest
from app.documents.exceptions import DocumentAccessDeniedError


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


class TestDocumentOwnershipIsolation:
    @pytest.mark.anyio
    async def test_user_a_cannot_view_user_b_document(self, db_session: Session):
        _seed_user(db_session, 2001)
        _seed_user(db_session, 2002)
        svc = DocumentService(db_session)

        # User A uploads
        doc_a = await svc.upload_document(
            user_id=2001,
            filename="user_a_file.txt",
            content_type="text/plain",
            data=b"user a content",
        )

        # User B attempts to access User A's document
        with pytest.raises(DocumentAccessDeniedError):
            svc.get_document(document_id=doc_a.id, user_id=2002)

    @pytest.mark.anyio
    async def test_user_a_cannot_delete_user_b_document(self, db_session: Session):
        _seed_user(db_session, 2003)
        _seed_user(db_session, 2004)
        svc = DocumentService(db_session)

        # User A uploads
        doc_a = await svc.upload_document(
            user_id=2003,
            filename="user_a_file.txt",
            content_type="text/plain",
            data=b"user a content",
        )

        # User B attempts to delete User A's document
        with pytest.raises(DocumentAccessDeniedError):
            await svc.delete_document(document_id=doc_a.id, user_id=2004)

    @pytest.mark.anyio
    async def test_user_a_cannot_process_user_b_document(self, db_session: Session):
        _seed_user(db_session, 2005)
        _seed_user(db_session, 2006)
        svc = DocumentService(db_session)

        # User A uploads
        doc_a = await svc.upload_document(
            user_id=2005,
            filename="user_a_file.txt",
            content_type="text/plain",
            data=b"user a content",
        )

        # User B attempts to trigger analysis on User A's document
        with pytest.raises(DocumentAccessDeniedError):
            await svc.process_document(document_id=doc_a.id, user_id=2006)

    @pytest.mark.anyio
    async def test_user_a_cannot_confirm_user_b_document_extraction(self, db_session: Session):
        _seed_user(db_session, 2007)
        _seed_user(db_session, 2008)
        
        doc_svc = DocumentService(db_session)
        import_svc = FinancialDocumentImportService(db_session)

        # User A uploads
        doc_a = await doc_svc.upload_document(
            user_id=2007,
            filename="user_a_file.txt",
            content_type="text/plain",
            data=b"user a content",
        )

        # User B attempts to confirm extraction for User A's document
        req = ConfirmationRequest(confirmed_fields=[], confirmed_transactions=[])
        with pytest.raises(DocumentAccessDeniedError):
            import_svc.confirm_and_import(
                document_id=doc_a.id,
                user_id=2008,
                req=req,
            )

    @pytest.mark.anyio
    async def test_list_documents_only_returns_owned_items(self, db_session: Session):
        _seed_user(db_session, 2009)
        _seed_user(db_session, 2010)
        svc = DocumentService(db_session)

        # User A uploads 2 files
        await svc.upload_document(
            user_id=2009,
            filename="file1.txt",
            content_type="text/plain",
            data=b"text content 1",
        )
        await svc.upload_document(
            user_id=2009,
            filename="file2.txt",
            content_type="text/plain",
            data=b"text content 2",
        )

        # User B uploads 1 file
        await svc.upload_document(
            user_id=2010,
            filename="file3.txt",
            content_type="text/plain",
            data=b"text content 3",
        )

        # Check list for A
        items_a, total_a = svc.list_documents(user_id=2009)
        assert total_a == 2
        assert all(d.user_id == 2009 for d in items_a)

        # Check list for B
        items_b, total_b = svc.list_documents(user_id=2010)
        assert total_b == 1
        assert all(d.user_id == 2010 for d in items_b)
