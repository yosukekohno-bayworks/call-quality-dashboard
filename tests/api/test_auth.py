"""
API tests for authentication endpoints.
"""
import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.services.auth import create_tokens, create_access_token, create_refresh_token


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestLoginEndpoint:
    """Tests for POST /api/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["tokens"]["access_token"] is not None
        assert data["tokens"]["refresh_token"] is not None
        assert data["tokens"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent email."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test login with inactive user."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "inactive@example.com", "password": "testpassword123"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Inactive user"

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Test login with invalid email format."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "not-an-email", "password": "password"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient):
        """Test login with missing password field."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_body(self, client: AsyncClient):
        """Test login with empty request body."""
        response = await client.post("/api/auth/login", json={})

        assert response.status_code == 422


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful registration with new tenant."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newpassword123",
                "name": "New User",
                "tenant_name": "New Company",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["role"] == UserRole.ADMIN.value  # First user is admin
        assert data["tokens"]["access_token"] is not None

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with already registered email."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "password": "password123",
                "name": "Another User",
                "tenant_name": "Another Company",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_without_tenant_name(self, client: AsyncClient):
        """Test registration without tenant name."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "name": "New User",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Tenant name is required for registration"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "name": "User",
                "tenant_name": "Company",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_required_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        response = await client.post(
            "/api/auth/register",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 422


class TestGoogleAuthEndpoint:
    """Tests for POST /api/auth/google endpoint."""

    @pytest.mark.asyncio
    async def test_google_auth_invalid_token(self, client: AsyncClient):
        """Test Google auth with invalid token."""
        response = await client.post(
            "/api/auth/google",
            json={"credential": "invalid-google-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid Google token"

    @pytest.mark.asyncio
    @patch("app.api.v1.auth.verify_google_token")
    async def test_google_auth_new_user(self, mock_verify, client: AsyncClient):
        """Test Google auth creates new user if not exists."""
        mock_verify.return_value = {
            "google_id": "new-google-id-999",
            "email": "newgoogleuser@example.com",
            "name": "New Google User",
            "email_verified": True,
        }

        response = await client.post(
            "/api/auth/google",
            json={"credential": "valid-google-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newgoogleuser@example.com"
        assert data["user"]["name"] == "New Google User"
        assert data["tokens"]["access_token"] is not None

    @pytest.mark.asyncio
    @patch("app.api.v1.auth.verify_google_token")
    async def test_google_auth_existing_user_by_google_id(
        self, mock_verify, client: AsyncClient, google_user: User
    ):
        """Test Google auth with existing user (matched by Google ID)."""
        mock_verify.return_value = {
            "google_id": "google-unique-id-123",  # Same as google_user
            "email": "google@example.com",
            "name": "Google User",
            "email_verified": True,
        }

        response = await client.post(
            "/api/auth/google",
            json={"credential": "valid-google-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "google@example.com"

    @pytest.mark.asyncio
    @patch("app.api.v1.auth.verify_google_token")
    async def test_google_auth_links_google_id_to_existing_email(
        self, mock_verify, client: AsyncClient, test_user: User
    ):
        """Test Google auth links Google ID to existing user by email."""
        mock_verify.return_value = {
            "google_id": "brand-new-google-id",
            "email": "test@example.com",  # Same as test_user
            "name": "Test User",
            "email_verified": True,
        }

        response = await client.post(
            "/api/auth/google",
            json={"credential": "valid-google-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    @patch("app.api.v1.auth.verify_google_token")
    async def test_google_auth_inactive_user(
        self, mock_verify, client: AsyncClient, inactive_user: User
    ):
        """Test Google auth with inactive user."""
        mock_verify.return_value = {
            "google_id": "inactive-google-id",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "email_verified": True,
        }

        response = await client.post(
            "/api/auth/google",
            json={"credential": "valid-google-token"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Inactive user"


class TestRefreshTokenEndpoint:
    """Tests for POST /api/auth/refresh endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh.

        Note: This test requires PostgreSQL due to UUID type handling.
        SQLite stores UUIDs as strings which causes comparison issues.
        """
        refresh_token = create_refresh_token(str(test_user.id))

        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        # New tokens should be different
        assert data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_refresh_token_using_access_token(self, client: AsyncClient, test_user: User):
        """Test refresh with access token (should fail)."""
        access_token = create_access_token(str(test_user.id))

        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_refresh_token_nonexistent_user(self, client: AsyncClient):
        """Test refresh with token for nonexistent user.

        Note: Requires PostgreSQL for UUID type handling.
        """
        refresh_token = create_refresh_token(str(uuid.uuid4()))

        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "User not found or inactive"

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_refresh_token_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test refresh with token for inactive user.

        Note: Requires PostgreSQL for UUID type handling.
        """
        refresh_token = create_refresh_token(str(inactive_user.id))

        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "User not found or inactive"


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        """Test successful logout."""
        response = await client.post("/api/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestMeEndpoint:
    """Tests for GET /api/auth/me endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_me_authenticated(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Test getting current user info when authenticated.

        Note: Requires PostgreSQL for UUID type handling.
        """
        response = await client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user info without authentication."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 403  # HTTPBearer returns 403 when no credentials

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client: AsyncClient):
        """Test getting current user info with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_expired_token(self, client: AsyncClient, test_user: User):
        """Test getting current user info with expired token (simulated)."""
        # Note: Creating actually expired tokens requires time manipulation
        # This tests the behavior with a malformed token
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxfQ.invalid"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_me_nonexistent_user_in_token(self, client: AsyncClient):
        """Test with token containing nonexistent user ID.

        Note: Requires PostgreSQL for UUID type handling.
        """
        token = create_access_token(str(uuid.uuid4()))
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401


class TestAuthorizationDependencies:
    """Tests for authorization dependencies (role-based access)."""

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_admin_can_access_protected_endpoint(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test that admin user can access protected endpoints.

        Note: Requires PostgreSQL for UUID type handling.
        """
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.requires_postgres
    async def test_operator_can_access_me_endpoint(
        self, client: AsyncClient, test_user_operator: User, operator_auth_headers: dict
    ):
        """Test that operator user can access /me endpoint.

        Note: Requires PostgreSQL for UUID type handling.
        """
        response = await client.get("/api/auth/me", headers=operator_auth_headers)
        assert response.status_code == 200
        assert response.json()["role"] == UserRole.OPERATOR.value
