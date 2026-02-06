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

# Patch UUID bind processor for SQLite compatibility
# When deps.py queries User.id == user_id (string from JWT),
# SQLAlchemy's UUID type tries to call .hex on the string and fails.
import sqlalchemy.types as sa_types

_orig_uuid_bind_processor = sa_types.Uuid.bind_processor


def _patched_uuid_bind_processor(self, dialect):
    orig = _orig_uuid_bind_processor(self, dialect)

    def process(value):
        if isinstance(value, str):
            import uuid as _uuid
            try:
                value = _uuid.UUID(value)
            except (ValueError, AttributeError):
                pass
        return orig(value) if orig else value

    return process


sa_types.Uuid.bind_processor = _patched_uuid_bind_processor

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
from app.models.operator import Operator
from app.models.operation_flow import OperationFlow
from app.models.call_record import CallRecord, AnalysisStatus
from app.models.analysis_result import AnalysisResult
from app.models.emotion_data import EmotionData
from app.models.analysis_prompt import AnalysisPrompt, PromptType
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


@pytest_asyncio.fixture
async def test_operator(db_session: AsyncSession, test_tenant: Tenant) -> Operator:
    """Create a test operator."""
    operator = Operator(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        biztel_operator_id="BIZ-OP-001",
        name="Test Operator Agent",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(operator)
    await db_session.commit()
    await db_session.refresh(operator)
    return operator


@pytest_asyncio.fixture
async def test_operation_flow(db_session: AsyncSession, test_tenant: Tenant) -> OperationFlow:
    """Create a test operation flow."""
    flow = OperationFlow(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Standard Inquiry Flow",
        classification_criteria="General customer inquiry about products or services",
        flow_definition={
            "steps": [
                {"id": "1", "name": "Greeting", "description": "Greet the customer"},
                {"id": "2", "name": "Identify", "description": "Identify the issue"},
                {"id": "3", "name": "Resolve", "description": "Resolve the issue"},
                {"id": "4", "name": "Closing", "description": "Close the call"},
            ]
        },
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(flow)
    await db_session.commit()
    await db_session.refresh(flow)
    return flow


@pytest_asyncio.fixture
async def test_call_record(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_operator: Operator,
) -> CallRecord:
    """Create a test call record."""
    call = CallRecord(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        biztel_id="BIZTEL-CALL-001",
        request_id="REQ-001",
        event_datetime=datetime(2024, 1, 15, 10, 30, 0),
        call_center_name="Support Center",
        call_center_extension="1001",
        business_label="Product Support",
        operator_id=test_operator.id,
        event_type="COMPLETEAGENT",
        caller_number="03-1234-5678",
        callee_number="0120-123-456",
        wait_time_seconds=15,
        talk_time_seconds=300,
        analysis_status=AnalysisStatus.COMPLETED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(call)
    await db_session.commit()
    await db_session.refresh(call)
    return call


@pytest_asyncio.fixture
async def test_analysis_result(
    db_session: AsyncSession,
    test_call_record: CallRecord,
) -> AnalysisResult:
    """Create a test analysis result."""
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        call_record_id=test_call_record.id,
        transcript="Customer: Hello, I need help with my order.\nAgent: Of course, I'd be happy to help.",
        flow_compliance=True,
        compliance_details={"steps_completed": 4, "steps_total": 4},
        overall_score=85.5,
        fillers_count=3,
        silence_duration=5.2,
        summary="Customer inquired about order status. Agent resolved successfully.",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


@pytest_asyncio.fixture
async def test_emotion_data(
    db_session: AsyncSession,
    test_analysis_result: AnalysisResult,
) -> EmotionData:
    """Create test emotion data."""
    emotion = EmotionData(
        id=uuid.uuid4(),
        analysis_id=test_analysis_result.id,
        timestamp=10.5,
        emotion_type="satisfaction",
        confidence=0.85,
        audio_features={"pitch": 220.0, "energy": 0.6},
        created_at=datetime.utcnow(),
    )
    db_session.add(emotion)
    await db_session.commit()
    await db_session.refresh(emotion)
    return emotion


@pytest_asyncio.fixture
async def test_analysis_prompt(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> AnalysisPrompt:
    """Create a test analysis prompt."""
    prompt = AnalysisPrompt(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        prompt_type=PromptType.QUALITY_SCORE,
        name="Quality Score Prompt",
        description="Evaluate call quality",
        prompt_text="Please evaluate the following call transcript for quality.",
        is_active=True,
        is_default=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(prompt)
    await db_session.commit()
    await db_session.refresh(prompt)
    return prompt


@pytest_asyncio.fixture
async def test_default_prompt(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> AnalysisPrompt:
    """Create a default analysis prompt (cannot be deleted)."""
    prompt = AnalysisPrompt(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        prompt_type=PromptType.SUMMARY,
        name="Default Summary Prompt",
        description="Default summary prompt",
        prompt_text="Summarize the following call transcript.",
        is_active=True,
        is_default=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(prompt)
    await db_session.commit()
    await db_session.refresh(prompt)
    return prompt


# Custom marker for tests that require PostgreSQL (UUID type support)
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_postgres: mark test as requiring PostgreSQL (UUID type support)"
    )
