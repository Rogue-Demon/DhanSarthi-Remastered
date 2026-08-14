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
        
        # Verify net_salary income candidate was created
        income_cands = proc_data["income_candidates"]
        assert len(income_cands) >= 1
        assert float(income_cands[0]["amount"]) == 75000.0

        # 4. Get extraction results endpoint
        ext_resp = client.get(
            f"/api/v1/documents/{doc_id}/extraction",
            headers=auth_headers["user_a"]
        )
        assert ext_resp.status_code == 200
        assert ext_resp.json()["document_type"] == "SALARY_SLIP"

        # 5. Confirm and import the net_salary income candidate
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_fields": [],
                "confirmed_transactions": [],
                "confirmed_income": proc_data["income_candidates"],
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_income_count"] == 1
        assert conf_data["status"] == "CONFIRMED"

        # 6. Delete document
        del_resp = client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers["user_a"]
        )
        assert del_resp.status_code == 204

    def test_salary_slip_all_fields_import_and_no_double_counting(self, client: TestClient, auth_headers: dict):
        """Test confirming net_salary, gross_salary, total_deductions, and salary_period."""
        # 1. Setup profile
        client.post(
            "/api/v1/profile",
            headers=auth_headers["user_a"],
            json={"display_name": "Salary User", "persona": "PROFESSIONAL", "country": "IN", "currency": "INR", "risk_profile": "MODERATE"}
        )

        # 2. Upload salary slip
        salary_slip_text = (
            "employer: Acme Corp\n"
            "gross salary: 100000\n"
            "net salary: 85000\n"
            "total deductions: 15000\n"
            "salary period: August 2026\n"
        )
        file_io = io.BytesIO(salary_slip_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("payslip_full.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        # 3. Process
        client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])

        # 4. Confirm all fields
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_fields": ["net_salary", "gross_salary", "total_deductions", "salary_period", "employer"],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_fields_count"] >= 4
        assert conf_data["status"] == "CONFIRMED"

        # Verify income was created with 85000 (net salary) and NOT double counted with 100000 (gross salary)
        income_resp = client.get("/api/v1/income", headers=auth_headers["user_a"])
        assert income_resp.status_code == 200
        data = income_resp.json()
        incomes_list = data["items"] if isinstance(data, dict) and "items" in data else data
        net_incomes = [i for i in incomes_list if float(i["amount"]) == 85000.0]
        gross_incomes = [i for i in incomes_list if float(i["amount"]) == 100000.0]
        assert len(net_incomes) == 1
        assert len(gross_incomes) == 0

    def test_salary_income_candidate_is_confirmed(self, client: TestClient, auth_headers: dict):
        """Verify salary slip with Gross 50000, Deductions 5000, Net 45000 creates 1 Income record and 0 transactions."""
        salary_text = (
            "employer: ABC Technologies Pvt. Ltd.\n"
            "gross salary: 50000\n"
            "total deductions: 5000\n"
            "net salary: 45000\n"
            "salary period: August 2026\n"
            "pay date: 31 August 2026\n"
        )
        file_io = io.BytesIO(salary_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("salary_aug2026.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])
        assert proc_resp.status_code == 200

        # Confirm fields
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_fields": ["net_salary", "gross_salary", "total_deductions", "salary_period", "employer"],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_income_count"] == 1
        assert conf_data["imported_transactions_count"] == 0
        assert conf_data["imported_metadata_count"] == 4

        # Verify DB Income record
        inc_resp = client.get("/api/v1/income", headers=auth_headers["user_a"])
        assert inc_resp.status_code == 200
        inc_data = inc_resp.json()
        inc_items = inc_data["items"] if isinstance(inc_data, dict) and "items" in inc_data else inc_data
        salary_45k = [i for i in inc_items if float(i["amount"]) == 45000.0]
        assert len(salary_45k) == 1
        assert "ABC Technologies" in salary_45k[0]["source"]

    def test_income_import_without_transaction_candidate(self, client: TestClient, auth_headers: dict):
        """Verify income_count == 1 and transaction_count == 0 when importing income candidate without transaction."""
        inc_candidate = {
            "source": "Consulting Fee",
            "amount": 25000.0,
            "income_date": "2026-08-31",
            "category": "Freelance",
            "currency": "INR"
        }
        salary_text = "statement document\n"
        file_io = io.BytesIO(salary_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("doc_income.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]
        client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])

        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_income": [inc_candidate],
                "confirmed_fields": [],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_income_count"] == 1
        assert conf_data["imported_transactions_count"] == 0

    def test_zero_import_result(self, client: TestClient, auth_headers: dict):
        """Test zero confirmed fields/transactions returns zero count result."""
        salary_slip_text = "basic salary: 50000\n"
        file_io = io.BytesIO(salary_slip_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("empty_confirm.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]
        client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])

        # Confirm with empty selections
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={"confirmed_fields": [], "confirmed_transactions": []}
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_fields_count"] == 0
        assert conf_data["imported_transactions_count"] == 0

    def test_universal_bill_expense_mapping(self, client: TestClient, auth_headers: dict):
        """Test utility bill document extraction and expense auto-import candidate."""
        bill_text = (
            "utility bill\n"
            "biller name: Tata Power\n"
            "total amount: 2450.00\n"
            "bill date: 10-08-2026\n"
        )
        file_io = io.BytesIO(bill_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("power_bill.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        # Process
        proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])
        assert proc_resp.status_code == 200
        proc_data = proc_resp.json()
        assert proc_data["document_type"] == "BILL"
        assert len(proc_data["expense_candidates"]) == 1
        assert float(proc_data["expense_candidates"][0]["amount"]) == 2450.0

        # Confirm expense candidate
        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_expenses": proc_data["expense_candidates"],
                "confirmed_fields": [],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_expense_count"] == 1

        # Verify expense record created
        exp_resp = client.get("/api/v1/expenses", headers=auth_headers["user_a"])
        assert exp_resp.status_code == 200
        exp_list = exp_resp.json()
        items = exp_list["items"] if isinstance(exp_list, dict) and "items" in exp_list else exp_list
        power_exp = [e for e in items if float(e["amount"]) == 2450.0]
        assert len(power_exp) == 1

    def test_universal_loan_liability_mapping(self, client: TestClient, auth_headers: dict):
        """Test loan statement extraction and liability candidate auto-import."""
        loan_text = (
            "loan account number: LA12345678\n"
            "lender: HDFC Bank\n"
            "principal amount: 1000000\n"
            "outstanding balance: 740000\n"
            "interest rate: 8.5%\n"
            "emi: 15500\n"
        )
        file_io = io.BytesIO(loan_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("homeloan.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])
        assert proc_resp.status_code == 200
        proc_data = proc_resp.json()
        assert proc_data["document_type"] == "LOAN_STATEMENT"
        assert len(proc_data["liability_candidates"]) == 1
        assert float(proc_data["liability_candidates"][0]["amount"]) == 740000.0

        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_liabilities": proc_data["liability_candidates"],
                "confirmed_fields": [],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_liability_count"] == 1

        # Verify liability created
        liab_resp = client.get("/api/v1/liabilities", headers=auth_headers["user_a"])
        assert liab_resp.status_code == 200
        liab_list = liab_resp.json()
        items = liab_list["items"] if isinstance(liab_list, dict) and "items" in liab_list else liab_list
        hdfc_liab = [l for l in items if float(l["outstanding_balance"]) == 740000.0]
        assert len(hdfc_liab) == 1

    def test_universal_investment_asset_mapping(self, client: TestClient, auth_headers: dict):
        """Test investment statement extraction and asset candidate auto-import."""
        inv_text = (
            "mutual fund statement\n"
            "folio number: 91028374/12\n"
            "scheme name: Axis Bluechip Fund\n"
            "invested amount: 100000\n"
            "current value: 145000\n"
        )
        file_io = io.BytesIO(inv_text.encode("utf-8"))
        upload_resp = client.post(
            "/api/v1/documents",
            headers=auth_headers["user_a"],
            files={"file": ("mf_statement.txt", file_io, "text/plain")}
        )
        doc_id = upload_resp.json()["id"]

        proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=auth_headers["user_a"])
        assert proc_resp.status_code == 200
        proc_data = proc_resp.json()
        assert proc_data["document_type"] == "INVESTMENT_STATEMENT"
        assert len(proc_data["asset_candidates"]) == 1
        assert float(proc_data["asset_candidates"][0]["value"]) == 145000.0

        confirm_resp = client.post(
            f"/api/v1/documents/{doc_id}/confirm",
            headers=auth_headers["user_a"],
            json={
                "confirmed_assets": proc_data["asset_candidates"],
                "confirmed_fields": [],
                "confirmed_transactions": []
            }
        )
        assert confirm_resp.status_code == 200
        conf_data = confirm_resp.json()
        assert conf_data["imported_asset_count"] == 1

        # Verify asset created
        asset_resp = client.get("/api/v1/assets", headers=auth_headers["user_a"])
        assert asset_resp.status_code == 200
        asset_list = asset_resp.json()
        items = asset_list["items"] if isinstance(asset_list, dict) and "items" in asset_list else asset_list
        mf_asset = [a for a in items if float(a["current_value"]) == 145000.0]
        assert len(mf_asset) == 1


