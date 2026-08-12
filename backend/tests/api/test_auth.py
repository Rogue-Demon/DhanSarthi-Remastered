"""Integration tests for user authentication and authorization endpoints."""

import os
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token
from app.main import app
from app.models.user import User
from app.models.profile import Profile


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Provide a TestClient that overrides only the DB session.

    This ensures we test the real JWT authentication dependencies,
    not the X-User-ID override from test_api_v1.py.
    """
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ===================================================================
# Registration tests
# ===================================================================

class TestRegistration:
    def test_registration_success(self, client: TestClient, db_session: Session):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com", "password": "securepassword123"},
        )
        assert response.status_code == 201
        data = response.json()

        # Check safe fields are returned
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

        # Check sensitive fields are NEVER leaked
        assert "password" not in data
        assert "password_hash" not in data
        assert "hashed_password" not in data

        # Check database records
        user = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert user is not None
        assert user.password_hash != "securepassword123"  # Must be hashed

        # Check default profile auto-provisioned
        profile = db_session.query(Profile).filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.display_name == "newuser"

    def test_registration_duplicate_email(self, client: TestClient):
        # Register user first time
        client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "password123"},
        )

        # Register again with same email
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "password456"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_registration_email_case_insensitivity(self, client: TestClient):
        # Register user with uppercase characters in email
        client.post(
            "/api/v1/auth/register",
            json={"email": "CaseInsensitive@Example.com", "password": "password123"},
        )

        # Register again with lowercase email
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "caseinsensitive@example.com", "password": "password456"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_registration_invalid_inputs(self, client: TestClient):
        # Weak password (less than 8 characters)
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "password": "weak"},
        )
        assert response.status_code == 422

        # Empty password
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "empty@example.com", "password": "   "},
        )
        assert response.status_code == 422

        # Invalid email format
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422


# ===================================================================
# Login tests
# ===================================================================

class TestLogin:
    def test_login_success(self, client: TestClient):
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "correctpassword"},
        )

        # Attempt login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "correctpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpwd@example.com", "password": "correctpassword"},
        )

        # Attempt login with incorrect password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpwd@example.com", "password": "incorrectpassword"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials."

    def test_login_unknown_email(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials."

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={"email": "inactive@example.com", "password": "password123"},
        )

        # Manually deactivate user in DB
        user = db_session.query(User).filter_by(email="inactive@example.com").first()
        user.is_active = False
        db_session.commit()

        # Attempt login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "User account is inactive."


# ===================================================================
# Token Security & Validation tests
# ===================================================================

class TestTokenSecurity:
    def test_token_contents(self, client: TestClient):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "contents@example.com", "password": "password123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "contents@example.com", "password": "password123"},
        )
        token = response.json()["access_token"]
        payload = decode_access_token(token)

        assert payload is not None
        # Must contain subject (user id)
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload

        # Must NOT contain password, hash or sensitive financial properties
        assert "password" not in payload
        assert "password_hash" not in payload
        assert "income" not in payload
        assert "net_worth" not in payload

    def test_protected_route_success(self, client: TestClient):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "protected@example.com", "password": "password123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "protected@example.com", "password": "password123"},
        )
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.get("/api/v1/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["country"] == "IN"

    def test_protected_route_missing_token(self, client: TestClient):
        response = client.get("/api/v1/profile")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required."

    def test_protected_route_invalid_token(self, client: TestClient):
        headers = {"Authorization": "Bearer invalid_token_value"}
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required."

    def test_protected_route_expired_token(self, client: TestClient):
        # Create token that expired 5 minutes ago
        expired_token = create_access_token(
            data={"sub": "999"},
            expires_delta=timedelta(minutes=-5),
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required."

    def test_protected_route_inactive_user_token(self, client: TestClient, db_session: Session):
        # Register, login, get token
        client.post(
            "/api/v1/auth/register",
            json={"email": "inactivejwt@example.com", "password": "password123"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "inactivejwt@example.com", "password": "password123"},
        )
        token = login_resp.json()["access_token"]

        # Deactivate user
        user = db_session.query(User).filter_by(email="inactivejwt@example.com").first()
        user.is_active = False
        db_session.commit()

        # Call route with valid token but inactive user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "User account is inactive."

    def test_get_me_success(self, client: TestClient):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "getme@example.com", "password": "password123"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "getme@example.com", "password": "password123"},
        )
        token = login_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == "getme@example.com"

    def test_logout_success(self, client: TestClient):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "logoutuser@example.com", "password": "password123"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "logoutuser@example.com", "password": "password123"},
        )
        token = login_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.json()["detail"] == "Logged out successfully."

