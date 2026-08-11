"""
Integration tests for the Document Intelligence REST API endpoints.
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.enums import DocumentStatus, DocumentType
from app.models.user import User


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient that overrides the DB dependency only."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, dict[str, str]]:
    """Register and login two separate users, returning their Authorization headers."""
    # User A
    client.post(
        "/api/v1/auth/register",
        json={"email": "doca@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "doca@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    # User B
    client.post(
        "/api/v1/auth/register",
        json={"email": "docb@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "docb@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


class TestDocumentsAPI:
    def test_upload_and_list_documents(self, client: TestClient, auth_headers: dict):
        # 1. Upload a text file as User A
        file_content = b"Some valid plain text statement content"
        file_io = io.BytesIO(file_content)
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("statement.txt", file_io, "text/plain")}
        )
        assert upload_resp.status_code == 201
        data = upload_resp.json()
        assert data["original_filename"] == "statement.txt"
        assert data["mime_type"] == "text/plain"
        assert data["status"] == "UPLOADED"
        doc_id = data["id"]

        # 2. List documents as User A
        list_resp = client.get("/api/v1/documents", headers=auth_headers["user_a"])
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["id"] == doc_id

        # 3. Get document details as User A
        get_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers["user_a"])
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == doc_id

        # 4. List/Get as User B should not return User A's document (IDOR isolation)
        list_b = client.get("/api/v1/documents", headers=auth_headers["user_b"])
        assert list_b.json()["total"] == 0

        get_b = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers["user_b"])
        assert get_b.status_code == 403

    def test_process_and_confirm_endpoints(self, client: TestClient, auth_headers: dict):
        # 1. Setup profile for User A to avoid dashboard generation error (Profile is required)
        client.post(
            "/api/v1/profile",
            headers=auth_headers["user_a"],
            json={
                "display_name": "Test User",
                "persona": "PROFESSIONAL",
                "country": "IN",
                "currency": "INR",
                "risk_profile": "MODERATE"
            }
        )

        # 2. Upload text document representing a salary slip
        salary_slip_text = (
            "basic salary: 80000\n"
            "net pay: 75000\n"
            "total deductions: 5000\n"
            "salary period: August 2026\n"
        )
        file_io = io.BytesIO(salary_slip_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("payslip.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        # 3. Process the document
        process_resp = client.post(
            f"/api/v1/documents/{doc_id}/process",
            headers=auth_headers["user_a"]
        )
        assert process_resp.status_code == 200
        proc_data = process_resp.json()
        assert proc_data["document_type"] == "SALARY_SLIP"
        
        # Verify net_salary field was extracted
        fields = {f["name"]: f for f in proc_data["fields"]}
        assert "net_salary" in fields
        assert float(fields["net_salary"]["value"]) == 75000.0

        # 4. Get extraction results endpoint
        ext_resp = client.get(
            f"/api/v1/documents/{doc_id}/extraction",
            headers=auth_headers["user_a"]
        )
        assert ext_resp.status_code == 200
        assert ext_resp.json()["document_type"] == "SALARY_SLIP"

        # 5. Confirm and import the net_salary
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_fields": ["net_salary"],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_fields_count"] == 1
        assert conf_data["status"] == "CONFIRMED"

        # 6. Delete document
        del_resp = client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers["user_a"]
        )
        assert del_resp.status_code == 204
