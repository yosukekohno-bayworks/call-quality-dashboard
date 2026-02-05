"""
Unit tests for data models.
"""
import uuid
from datetime import datetime

import pytest

from app.models.user import User, UserRole
from app.models.tenant import Tenant


class TestUserRole:
    """Tests for UserRole enum."""

    def test_user_role_values(self):
        """Test UserRole enum has expected values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.SV.value == "sv"
        assert UserRole.QA.value == "qa"
        assert UserRole.OPERATOR.value == "operator"
        assert UserRole.EXECUTIVE.value == "executive"

    def test_user_role_is_string_enum(self):
        """Test UserRole is a string enum."""
        assert isinstance(UserRole.ADMIN.value, str)
        assert str(UserRole.ADMIN) == "UserRole.ADMIN"

    def test_user_role_member_count(self):
        """Test UserRole has exactly 5 members."""
        assert len(UserRole) == 5


class TestUserModel:
    """Tests for User model."""

    def test_user_creation_with_defaults(self):
        """Test creating User with default values."""
        tenant_id = uuid.uuid4()
        user = User(
            tenant_id=tenant_id,
            email="user@example.com",
            name="Test User",
        )

        assert user.email == "user@example.com"
        assert user.name == "Test User"
        assert user.tenant_id == tenant_id
        assert user.role == UserRole.OPERATOR  # Default role
        assert user.is_active is True
        assert user.password_hash is None
        assert user.google_id is None

    def test_user_creation_with_all_fields(self):
        """Test creating User with all fields specified."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.utcnow()

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="admin@example.com",
            password_hash="hashed_password",
            google_id="google-123",
            role=UserRole.ADMIN,
            name="Admin User",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        assert user.id == user_id
        assert user.tenant_id == tenant_id
        assert user.email == "admin@example.com"
        assert user.password_hash == "hashed_password"
        assert user.google_id == "google-123"
        assert user.role == UserRole.ADMIN
        assert user.name == "Admin User"
        assert user.is_active is True

    def test_user_auto_generates_uuid(self):
        """Test that User auto-generates UUID if not provided."""
        user = User(
            tenant_id=uuid.uuid4(),
            email="user@example.com",
            name="Test User",
        )

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)

    def test_user_different_roles(self):
        """Test creating users with different roles."""
        tenant_id = uuid.uuid4()

        for role in UserRole:
            user = User(
                tenant_id=tenant_id,
                email=f"{role.value}@example.com",
                name=f"{role.value.title()} User",
                role=role,
            )
            assert user.role == role


class TestTenantModel:
    """Tests for Tenant model."""

    def test_tenant_creation_with_defaults(self):
        """Test creating Tenant with default values."""
        tenant = Tenant(name="Test Company")

        assert tenant.name == "Test Company"
        assert tenant.is_active is True
        assert tenant.biztel_api_key is None
        assert tenant.biztel_api_secret is None
        assert tenant.biztel_base_url is None

    def test_tenant_creation_with_all_fields(self):
        """Test creating Tenant with all fields specified."""
        tenant_id = uuid.uuid4()
        now = datetime.utcnow()

        tenant = Tenant(
            id=tenant_id,
            name="Enterprise Corp",
            biztel_api_key="api-key-123",
            biztel_api_secret="api-secret-456",
            biztel_base_url="https://api.biztel.example.com",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        assert tenant.id == tenant_id
        assert tenant.name == "Enterprise Corp"
        assert tenant.biztel_api_key == "api-key-123"
        assert tenant.biztel_api_secret == "api-secret-456"
        assert tenant.biztel_base_url == "https://api.biztel.example.com"
        assert tenant.is_active is True

    def test_tenant_auto_generates_uuid(self):
        """Test that Tenant auto-generates UUID if not provided."""
        tenant = Tenant(name="Auto UUID Company")

        assert tenant.id is not None
        assert isinstance(tenant.id, uuid.UUID)

    def test_tenant_inactive(self):
        """Test creating inactive tenant."""
        tenant = Tenant(name="Inactive Company", is_active=False)

        assert tenant.is_active is False
