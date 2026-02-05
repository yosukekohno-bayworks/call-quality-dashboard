"""
Pytest configuration and fixtures for backend tests.
"""
import os

# Set test environment variables BEFORE importing any app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"

# Patch JSONB to JSON for SQLite compatibility BEFORE any model imports
from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import sqlalchemy.dialects.postgresql as pg_dialect
pg_dialect.JSONB = JSON

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event
from sqlmodel import SQLModel

from app.main import app
from app.api.deps import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.services.auth import create_tokens, get_password_hash


# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Company",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user with password."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_operator(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user with OPERATOR role."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="operator@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test Operator",
        role=UserRole.OPERATOR,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create an inactive test user."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="inactive@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Inactive User",
        role=UserRole.OPERATOR,
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def google_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user authenticated via Google."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="google@example.com",
        google_id="google-unique-id-123",
        name="Google User",
        role=UserRole.OPERATOR,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Generate authorization headers for test user."""
    tokens = create_tokens(str(test_user.id))
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def operator_auth_headers(test_user_operator: User) -> dict[str, str]:
    """Generate authorization headers for operator user."""
    tokens = create_tokens(str(test_user_operator.id))
    return {"Authorization": f"Bearer {tokens.access_token}"}


def create_auth_headers_for_user(user: User) -> dict[str, str]:
    """Helper function to create auth headers for any user."""
    tokens = create_tokens(str(user.id))
    return {"Authorization": f"Bearer {tokens.access_token}"}


# Custom marker for tests that require PostgreSQL (UUID type support)
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_postgres: mark test as requiring PostgreSQL (UUID type support)"
    )
