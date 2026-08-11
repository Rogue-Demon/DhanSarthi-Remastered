"""
Tests for document upload validation, file size limits, MIME matches,
malicious filenames, and duplicate detection.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.enums import DocumentStatus
from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile
from app.services.document_service import DocumentService
from app.documents.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    InvalidDocumentError,
    DuplicateDocumentError,
)


def _seed_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"upload_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"Upload User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


class TestDocumentUploadValidation:
    @pytest.mark.anyio
    async def test_upload_valid_pdf(self, db_session: Session):
        _seed_user(db_session, 1001)
        svc = DocumentService(db_session)

        # Mock standard PDF signature
        pdf_data = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj"
        doc = await svc.upload_document(
            user_id=1001,
            filename="statement.pdf",
            content_type="application/pdf",
            data=pdf_data,
        )

        assert doc.id is not None
        assert doc.user_id == 1001
        assert doc.original_filename == "statement.pdf"
        assert doc.mime_type == "application/pdf"
        assert doc.status == DocumentStatus.UPLOADED

    @pytest.mark.anyio
    async def test_upload_mismatched_magic_bytes_raises(self, db_session: Session):
        _seed_user(db_session, 1002)
        svc = DocumentService(db_session)

        # File claiming to be PDF but contains arbitrary text
        fake_pdf = b"not a pdf file content"
        with pytest.raises(InvalidDocumentError):
            await svc.upload_document(
                user_id=1002,
                filename="fake.pdf",
                content_type="application/pdf",
                data=fake_pdf,
            )

    @pytest.mark.anyio
    async def test_upload_unsupported_format_raises(self, db_session: Session):
        _seed_user(db_session, 1003)
        svc = DocumentService(db_session)

        with pytest.raises(UnsupportedFileTypeError):
            await svc.upload_document(
                user_id=1003,
                filename="script.exe",
                content_type="application/octet-stream",
                data=b"\x00\x00\x00\x00",
            )

    @pytest.mark.anyio
    async def test_upload_oversized_file_raises(self, db_session: Session, monkeypatch):
        _seed_user(db_session, 1004)
        svc = DocumentService(db_session)

        # Temporarily mock size limit config to 1 MB
        from app.core.config import settings
        monkeypatch.setattr(settings, "max_document_size_mb", 1)

        # 2 MB payload
        large_data = b"0" * (2 * 1024 * 1024)
        with pytest.raises(FileTooLargeError):
            await svc.upload_document(
                user_id=1004,
                filename="big_file.txt",
                content_type="text/plain",
                data=large_data,
            )

    @pytest.mark.anyio
    async def test_upload_empty_file_raises(self, db_session: Session):
        _seed_user(db_session, 1005)
        svc = DocumentService(db_session)

        with pytest.raises(InvalidDocumentError):
            await svc.upload_document(
                user_id=1005,
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )

    @pytest.mark.anyio
    async def test_upload_duplicate_checksum_raises(self, db_session: Session):
        _seed_user(db_session, 1006)
        svc = DocumentService(db_session)

        text_data = b"Some unique text payload for testing duplicates."
        # First upload
        await svc.upload_document(
            user_id=1006,
            filename="doc1.txt",
            content_type="text/plain",
            data=text_data,
        )

        # Second upload with same content
        with pytest.raises(DuplicateDocumentError):
            await svc.upload_document(
                user_id=1006,
                filename="doc2.txt",
                content_type="text/plain",
                data=text_data,
            )

    @pytest.mark.anyio
    async def test_sanitize_filename_traversal(self, db_session: Session):
        _seed_user(db_session, 1007)
        svc = DocumentService(db_session)

        doc = await svc.upload_document(
            user_id=1007,
            filename="../../../../etc/passwd.txt",
            content_type="text/plain",
            data=b"safe text content",
        )
        assert ".." not in doc.original_filename
        assert "/" not in doc.original_filename
