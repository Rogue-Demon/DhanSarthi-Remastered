import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.models.profile import Profile


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Provide a TestClient that overrides only the DB session.

    This ensures we test the real JWT authentication dependencies.
    """
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestProfileAPI:
    def _register_and_login(self, client: TestClient, email: str) -> str:
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "securepassword123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "securepassword123"},
        )
        return response.json()["access_token"]

    def test_unauthenticated_profile_retrieval(self, client: TestClient):
        # 1. Unauthenticated profile retrieval -> 401
        response = client.get("/api/v1/profile")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_authenticated_profile_retrieval(self, client: TestClient):
        # 2. Authenticated profile retrieval -> 200 with default fields
        token = self._register_and_login(client, "user1@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert data["display_name"] == "user1"
        assert data["country"] == "IN" or data["country"] == "IND"
        assert data["phone"] is None
        assert data["occupation"] is None

    def test_profile_update_success(self, client: TestClient):
        # 3. Profile update -> 200 with updated fields
        token = self._register_and_login(client, "user2@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # First verify it's empty
        response = client.get("/api/v1/profile", headers=headers)
        assert response.json()["phone"] is None

        # Update fields
        update_data = {
            "display_name": "Updated Name",
            "phone": "+919876543210",
            "occupation": "Software Engineer",
            "country": "IND",
            "currency": "INR"
        }
        patch_response = client.patch("/api/v1/profile", json=update_data, headers=headers)
        assert patch_response.status_code == 200
        patched_data = patch_response.json()
        assert patched_data["display_name"] == "Updated Name"
        assert patched_data["phone"] == "+919876543210"
        assert patched_data["occupation"] == "Software Engineer"
        assert patched_data["country"] == "IND"
        assert patched_data["currency"] == "INR"

        # 7. Persistence Check: Retrieve again to check it persisted in database
        get_response = client.get("/api/v1/profile", headers=headers)
        assert get_response.status_code == 200
        persisted_data = get_response.json()
        assert persisted_data["display_name"] == "Updated Name"
        assert persisted_data["phone"] == "+919876543210"
        assert persisted_data["occupation"] == "Software Engineer"

    def test_invalid_profile_update(self, client: TestClient):
        # 4. Invalid profile update -> 422 validation error
        token = self._register_and_login(client, "user3@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # Display name too long (> 100 characters)
        invalid_data = {
            "display_name": "A" * 101
        }
        response = client.patch("/api/v1/profile", json=invalid_data, headers=headers)
        assert response.status_code == 422

        # Phone too long (> 20 characters)
        invalid_phone = {
            "phone": "1" * 21
        }
        response = client.patch("/api/v1/profile", json=invalid_phone, headers=headers)
        assert response.status_code == 422

    def test_user_isolation(self, client: TestClient, db_session: Session):
        # 5. User isolation: User A updates profile; User B sees only their own profile
        token_a = self._register_and_login(client, "usera@example.com")
        token_b = self._register_and_login(client, "userb@example.com")

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A updates profile
        client.patch(
            "/api/v1/profile",
            json={"display_name": "User A Name", "phone": "+123456"},
            headers=headers_a
        )

        # User B fetches profile
        response_b = client.get("/api/v1/profile", headers=headers_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert data_b["display_name"] == "userb"
        assert data_b["phone"] is None

        # Verify database isolation directly
        user_a = db_session.query(User).filter_by(email="usera@example.com").first()
        user_b = db_session.query(User).filter_by(email="userb@example.com").first()

        profile_a = db_session.query(Profile).filter_by(user_id=user_a.id).first()
        profile_b = db_session.query(Profile).filter_by(user_id=user_b.id).first()

        assert profile_a.display_name == "User A Name"
        assert profile_b.display_name == "userb"

    def test_unauthorized_update(self, client: TestClient):
        # 6. Unauthorized update -> 401
        response = client.patch(
            "/api/v1/profile",
            json={"display_name": "Some Name"}
        )
        assert response.status_code == 401
