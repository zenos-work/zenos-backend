"""
Test suite for Users API
Run with: pytest tests/test_users.py -v
"""

import pytest
from models.user.model import User
from models.user.requests import UpdateProfileRequest, UpdateRoleRequest
from models.common.enums import Scope, UserRole
import api.users.handler as users_handler


class TestUserModel:
    """Test User model scope-based serialization."""

    @pytest.fixture
    def sample_user(self):
        return User(
            id="user-123",
            email="alice@example.com",
            name="Alice Author",
            role=UserRole.AUTHOR,
            avatar_url="https://media.zenos.work/uploads/avatar.jpg",
            google_id="google-id-456",
            is_active=1,
            created_at="2026-01-15T10:30:00Z",
            updated_at="2026-03-16T14:22:00Z",
        )

    def test_public_scope_excludes_sensitive_fields(self, sample_user):
        data = sample_user.to_dict(Scope.PUBLIC)
        assert "id" in data
        assert "name" in data
        assert "avatar_url" in data
        assert "role" in data
        assert "created_at" in data
        # Sensitive fields excluded
        assert "email" not in data
        assert "google_id" not in data
        assert "is_active" not in data

    def test_private_scope_includes_email(self, sample_user):
        data = sample_user.to_dict(Scope.PRIVATE)
        assert "email" in data
        assert data["email"] == "alice@example.com"
        # But not admin fields
        assert "google_id" not in data

    def test_private_scope_includes_terms_acceptance_timestamp(self, sample_user):
        sample_user.terms_accepted_at = "2026-03-18T10:00:00Z"
        data = sample_user.to_dict(Scope.PRIVATE)
        assert "terms_accepted_at" in data
        assert data["terms_accepted_at"] == "2026-03-18T10:00:00Z"

    def test_admin_scope_includes_all_fields(self, sample_user):
        data = sample_user.to_dict(Scope.ADMIN)
        assert "email" in data
        assert "google_id" in data
        assert "is_active" in data
        assert data["google_id"] == "google-id-456"

    def test_null_avatar_not_included(self, sample_user):
        sample_user.avatar_url = None
        data = sample_user.to_dict(Scope.PRIVATE)
        assert "avatar_url" not in data


class TestUpdateProfileRequest:
    """Test profile update request validation."""

    def test_valid_name_update(self):
        req = UpdateProfileRequest.from_body({"name": "Alice Brown"})
        assert req.name == "Alice Brown"
        assert req.avatar_url is None

    def test_valid_avatar_update(self):
        req = UpdateProfileRequest.from_body(
            {"avatar_url": "https://example.com/new-avatar.jpg"}
        )
        assert req.name is None
        assert req.avatar_url == "https://example.com/new-avatar.jpg"

    def test_valid_both_update(self):
        req = UpdateProfileRequest.from_body(
            {"name": "Alice", "avatar_url": "https://example.com/avatar.jpg"}
        )
        assert req.name == "Alice"
        assert req.avatar_url == "https://example.com/avatar.jpg"

    def test_rejects_empty_update(self):
        with pytest.raises(ValueError, match="At least name or avatar_url"):
            UpdateProfileRequest.from_body({})

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            UpdateProfileRequest.from_body({"name": ""})

    def test_rejects_long_name(self):
        with pytest.raises(ValueError, match="cannot be longer than 100"):
            UpdateProfileRequest.from_body({"name": "a" * 101})


class TestUpdateRoleRequest:
    """Test role update request validation."""

    def test_valid_author_role(self):
        req = UpdateRoleRequest.from_body({"role": "AUTHOR"})
        assert req.role == "AUTHOR"

    def test_valid_approver_role(self):
        req = UpdateRoleRequest.from_body({"role": "APPROVER"})
        assert req.role == "APPROVER"

    def test_case_insensitive_role(self):
        req = UpdateRoleRequest.from_body({"role": "author"})
        assert req.role == "AUTHOR"

    def test_rejects_invalid_role(self):
        with pytest.raises(ValueError, match="Invalid role"):
            UpdateRoleRequest.from_body({"role": "INVALID"})

    def test_rejects_missing_role(self):
        with pytest.raises(ValueError, match="Role is required"):
            UpdateRoleRequest.from_body({})


class TestUserService:
    """Test UserService business logic (requires mock DB)."""

    @pytest.fixture
    async def mock_env(self):
        """Mock Cloudflare environment."""

        class MockDB:
            async def prepare(self, sql):
                return self

            def bind(self, *args):
                return self

            async def run(self):
                return None

            async def first(self):
                return None

            async def all(self):
                return []

        class MockEnv:
            DB = MockDB()

        return MockEnv()

    @pytest.mark.asyncio
    async def test_get_user_by_id_public_scope(self, mock_env):
        """Test retrieving public user profile."""
        # This would actually query the DB (mocked above)
        # user = await svc.get_by_id("user-123", scope=Scope.PUBLIC)
        # assert user is not None
        pass  # TODO: Implement with proper mocking


# Integration Tests (require running backend)


class TestUsersEndpoints:
    """Integration tests for user endpoints."""

    def test_get_public_profile(self, client):
        """GET /api/users/:id"""
        response = client.get("/api/users/user-123")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "AUTHOR"
        assert "email" not in data["user"]  # Private field excluded
        assert "google_id" not in data["user"]

    def test_get_public_profile_returns_404_for_missing_user(self, client):
        response = client.get("/api/users/missing-user")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_get_authenticated_user(self, client, auth_token):
        """GET /api/users/me"""
        response = client.get(
            "/api/users/me", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data["user"]  # Private field included
        assert data["user"]["terms_accepted_at"] == "2026-03-18T10:00:00Z"
        assert "google_id" not in data["user"]

    def test_get_authenticated_user_requires_auth(self, client):
        response = client.get("/api/users/me")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORISED"

    def test_update_profile(self, client, auth_token, fake_env):
        """PUT /api/users/me"""
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Alice Brown"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        assert fake_env.state["users"]["auth-user"].name == "Alice Brown"
        assert fake_env.state["profile_updates"][-1]["name"] == "Alice Brown"

    def test_update_profile_avatar_only_preserves_name(
        self, client, auth_token, fake_env
    ):
        """PUT /api/users/me avatar-only should skip name update"""
        original_name = fake_env.state["users"]["auth-user"].name
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "avatar_url": "https://api.dicebear.com/9.x/adventurer/svg?seed=ZenosAtlas"
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        assert fake_env.state["users"]["auth-user"].name == original_name
        assert fake_env.state["users"]["auth-user"].avatar_url.endswith(
            "seed=ZenosAtlas"
        )
        assert fake_env.state["profile_updates"][-1]["skip_name_update"] is True

    def test_upload_avatar(self, client, auth_token, fake_env):
        """POST /api/users/me/avatar"""
        image_data = b"fake image data"
        response = client.post(
            "/api/users/me/avatar",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "image/jpeg",
            },
            data=image_data,
        )
        assert response.status_code == 201
        assert "avatar_url" in response.json()
        assert "media.zenos.work" in response.json()["avatar_url"]
        assert response.json()["key"] == "uploads/auth-user.jpg"
        assert fake_env.state["uploads"][-1]["content_type"] == "image/jpeg"
        assert fake_env.state["users"]["auth-user"].avatar_url.endswith(
            "/auth-user.jpg"
        )

    def test_list_users_requires_admin(self, client, auth_token_reader):
        """GET /api/users (admin only)"""
        response = client.get(
            "/api/users", headers={"Authorization": f"Bearer {auth_token_reader}"}
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    def test_list_users_admin(self, client, auth_token_superadmin):
        """GET /api/users (superadmin)"""
        response = client.get(
            "/api/users?page=1&limit=2",
            headers={"Authorization": f"Bearer {auth_token_superadmin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 2
        assert data["pagination"]["total"] >= len(data["data"])
        assert data["pagination"]["pages"] >= 1

    def test_ban_user_requires_superadmin(self, client, auth_token_approver):
        """PUT /api/users/:id/ban (superadmin only)"""
        response = client.put(
            "/api/users/user-123/ban",
            headers={"Authorization": f"Bearer {auth_token_approver}"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    def test_ban_user_superadmin(self, client, auth_token_superadmin, fake_env):
        """PUT /api/users/:id/ban"""
        response = client.put(
            "/api/users/user-123/ban",
            headers={"Authorization": f"Bearer {auth_token_superadmin}"},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False
        assert fake_env.state["users"]["user-123"].is_active == 0

    def test_accept_terms_returns_existing_timestamp(
        self, client, auth_token, fake_env
    ):
        response = client.put(
            "/api/users/me/accept-terms",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["terms_accepted"] is True
        assert (
            data["terms_accepted_at"]
            == fake_env.state["users"]["auth-user"].terms_accepted_at
        )

    def test_accept_terms_sets_timestamp_when_missing(
        self, client, auth_token_reader, fake_env
    ):
        fake_env.state["users"]["reader-user"].terms_accepted_at = None

        response = client.put(
            "/api/users/me/accept-terms",
            headers={"Authorization": f"Bearer {auth_token_reader}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["terms_accepted"] is True
        assert data["terms_accepted_at"] == "2026-03-18T12:00:00Z"
        assert (
            fake_env.state["users"]["reader-user"].terms_accepted_at
            == "2026-03-18T12:00:00Z"
        )

    def test_list_approvers_for_author(self, client, auth_token):
        response = client.get(
            "/api/users/approvers",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "approvers" in data
        assert all(
            item["role"] in ["SUPERADMIN", "APPROVER"] for item in data["approvers"]
        )

    def test_send_approval_message_to_group(self, client, auth_token, monkeypatch):
        created_notifications = []

        class FakeAdminService:
            def __init__(self, _env, _ctx):
                pass

            async def create_notification(self, **kwargs):
                created_notifications.append(kwargs)

        monkeypatch.setattr(users_handler, "AdminService", FakeAdminService)

        response = client.post(
            "/api/users/approvers/message",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "mode": "group",
                "article_id": "a1",
                "message": "Please review this today",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sent"
        assert response.json()["recipients"] >= 1
        assert len(created_notifications) >= 1
        assert all("Approval chat" in item["message"] for item in created_notifications)

    def test_send_approval_message_to_individual_requires_recipient(
        self, client, auth_token
    ):
        response = client.post(
            "/api/users/approvers/message",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "mode": "individual",
                "article_id": "a1",
                "message": "Please review this",
                "recipient_ids": [],
            },
        )

        assert response.status_code == 422
        assert response.json()["error"]["message"] == "Select at least one approver"
