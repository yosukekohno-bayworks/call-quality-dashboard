"""
Unit tests for authentication service.
"""
import os

# Set test environment before imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"

# Patch JSONB to JSON for SQLite compatibility
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect
pg_dialect.JSONB = JSON

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.auth import Token, TokenPayload
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_tokens,
    decode_token,
    verify_google_token,
    authenticate_user,
    get_user_by_email,
    get_user_by_google_id,
    create_user,
    create_tenant,
    get_or_create_tenant_for_google_user,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_get_password_hash_returns_hash(self):
        """Test that get_password_hash returns a bcrypt hash."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_get_password_hash_different_for_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_password(self):
        """Test verify_password with empty password."""
        hashed = get_password_hash("realpassword")
        assert verify_password("", hashed) is False

    def test_hash_special_characters(self):
        """Test hashing passwords with special characters."""
        password = "p@$$w0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_hash_unicode_password(self):
        """Test hashing passwords with unicode characters."""
        password = "パスワード123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test that create_access_token returns a valid JWT."""
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_refresh_token(self):
        """Test that create_refresh_token returns a valid JWT."""
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        assert len(token.split(".")) == 3

    def test_create_tokens_returns_both(self):
        """Test that create_tokens returns both access and refresh tokens."""
        user_id = str(uuid.uuid4())
        tokens = create_tokens(user_id)

        assert isinstance(tokens, Token)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    def test_decode_access_token(self):
        """Test decoding a valid access token."""
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "access"
        assert payload.exp > datetime.utcnow().timestamp()

    def test_decode_refresh_token(self):
        """Test decoding a valid refresh token."""
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_empty_token(self):
        """Test decoding an empty token returns None."""
        payload = decode_token("")
        assert payload is None

    def test_decode_malformed_token(self):
        """Test decoding a malformed token returns None."""
        payload = decode_token("not-a-jwt")
        assert payload is None

    def test_access_token_has_correct_expiry(self):
        """Test that access token has approximately correct expiry time."""
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        payload = decode_token(token)

        # Should expire in approximately 15 minutes (allowing 2 minute tolerance)
        # Use UTC timestamp for comparison
        expected_expiry = datetime.utcnow() + timedelta(minutes=15)
        actual_expiry = datetime.utcfromtimestamp(payload.exp)

        assert abs((expected_expiry - actual_expiry).total_seconds()) < 120

    def test_refresh_token_has_correct_expiry(self):
        """Test that refresh token has approximately correct expiry time."""
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        # Should expire in approximately 7 days (allowing 2 minute tolerance)
        # Use UTC timestamp for comparison
        expected_expiry = datetime.utcnow() + timedelta(days=7)
        actual_expiry = datetime.utcfromtimestamp(payload.exp)

        assert abs((expected_expiry - actual_expiry).total_seconds()) < 120


class TestGoogleTokenVerification:
    """Tests for Google OAuth token verification."""

    def test_verify_google_token_invalid(self):
        """Test that invalid Google token returns None."""
        result = verify_google_token("invalid-token")
        assert result is None

    def test_verify_google_token_empty(self):
        """Test that empty Google token returns None."""
        result = verify_google_token("")
        assert result is None

    @patch("app.services.auth.id_token.verify_oauth2_token")
    def test_verify_google_token_valid(self, mock_verify):
        """Test that valid Google token returns user info."""
        mock_verify.return_value = {
            "iss": "accounts.google.com",
            "sub": "google-user-id-123",
            "email": "user@gmail.com",
            "name": "Test User",
            "email_verified": True,
        }

        result = verify_google_token("valid-token")

        assert result is not None
        assert result["google_id"] == "google-user-id-123"
        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"
        assert result["email_verified"] is True

    @patch("app.services.auth.id_token.verify_oauth2_token")
    def test_verify_google_token_wrong_issuer(self, mock_verify):
        """Test that token with wrong issuer returns None."""
        mock_verify.return_value = {
            "iss": "fake.issuer.com",
            "sub": "google-user-id-123",
            "email": "user@gmail.com",
        }

        result = verify_google_token("valid-token")
        assert result is None

    @patch("app.services.auth.id_token.verify_oauth2_token")
    def test_verify_google_token_https_issuer(self, mock_verify):
        """Test that token with https issuer is accepted."""
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "google-user-id-123",
            "email": "user@gmail.com",
            "name": "Test User",
        }

        result = verify_google_token("valid-token")

        assert result is not None
        assert result["google_id"] == "google-user-id-123"

    @patch("app.services.auth.id_token.verify_oauth2_token")
    def test_verify_google_token_no_name_uses_email(self, mock_verify):
        """Test that missing name falls back to email username."""
        mock_verify.return_value = {
            "iss": "accounts.google.com",
            "sub": "google-user-id-123",
            "email": "testuser@gmail.com",
        }

        result = verify_google_token("valid-token")

        assert result is not None
        assert result["name"] == "testuser"


class TestDatabaseOperations:
    """Tests for database operations in auth service."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user authentication."""
        user = await authenticate_user(db_session, "test@example.com", "testpassword123")

        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, test_user: User):
        """Test authentication with wrong password."""
        user = await authenticate_user(db_session, "test@example.com", "wrongpassword")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session: AsyncSession):
        """Test authentication with nonexistent email."""
        user = await authenticate_user(db_session, "nonexistent@example.com", "password")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_exists(self, db_session: AsyncSession, test_user: User):
        """Test getting user by email when user exists."""
        user = await get_user_by_email(db_session, "test@example.com")

        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_exists(self, db_session: AsyncSession):
        """Test getting user by email when user doesn't exist."""
        user = await get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_google_id_exists(self, db_session: AsyncSession, google_user: User):
        """Test getting user by Google ID when user exists."""
        user = await get_user_by_google_id(db_session, "google-unique-id-123")

        assert user is not None
        assert user.id == google_user.id

    @pytest.mark.asyncio
    async def test_get_user_by_google_id_not_exists(self, db_session: AsyncSession):
        """Test getting user by Google ID when user doesn't exist."""
        user = await get_user_by_google_id(db_session, "nonexistent-google-id")
        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_with_password(self, db_session: AsyncSession, test_tenant: Tenant):
        """Test creating a user with password."""
        user = await create_user(
            db_session,
            email="newuser@example.com",
            name="New User",
            password="password123",
            tenant_id=test_tenant.id,
            role=UserRole.OPERATOR,
        )

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.password_hash is not None
        assert user.google_id is None
        assert user.role == UserRole.OPERATOR

    @pytest.mark.asyncio
    async def test_create_user_with_google_id(self, db_session: AsyncSession, test_tenant: Tenant):
        """Test creating a user with Google ID."""
        user = await create_user(
            db_session,
            email="googleuser@example.com",
            name="Google User",
            google_id="new-google-id-456",
            tenant_id=test_tenant.id,
        )

        assert user is not None
        assert user.email == "googleuser@example.com"
        assert user.google_id == "new-google-id-456"
        assert user.password_hash is None

    @pytest.mark.asyncio
    async def test_create_tenant(self, db_session: AsyncSession):
        """Test creating a new tenant."""
        tenant = await create_tenant(db_session, "New Company")

        assert tenant is not None
        assert tenant.name == "New Company"
        assert tenant.is_active is True

    @pytest.mark.asyncio
    async def test_get_or_create_tenant_creates_new(self, db_session: AsyncSession):
        """Test get_or_create_tenant creates new tenant for new domain."""
        tenant = await get_or_create_tenant_for_google_user(db_session, "user@newdomain.com")

        assert tenant is not None
        assert tenant.name == "newdomain.com"

    @pytest.mark.asyncio
    async def test_get_or_create_tenant_returns_existing(self, db_session: AsyncSession):
        """Test get_or_create_tenant returns existing tenant."""
        # Create tenant first
        await create_tenant(db_session, "existingdomain.com")

        # Try to get or create for same domain
        tenant = await get_or_create_tenant_for_google_user(db_session, "user@existingdomain.com")

        assert tenant is not None
        assert tenant.name == "existingdomain.com"
