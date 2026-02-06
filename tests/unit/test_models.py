"""
Unit tests for data models.
"""
import uuid
from datetime import datetime

import pytest

from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.operator import Operator
from app.models.operation_flow import OperationFlow
from app.models.call_record import CallRecord, AnalysisStatus
from app.models.analysis_result import AnalysisResult
from app.models.emotion_data import EmotionData


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


class TestOperatorModel:
    """Tests for Operator model."""

    def test_operator_creation_with_defaults(self):
        """Test creating Operator with default values."""
        tenant_id = uuid.uuid4()
        operator = Operator(
            tenant_id=tenant_id,
            biztel_operator_id="BIZ-001",
            name="Operator One",
        )

        assert operator.tenant_id == tenant_id
        assert operator.biztel_operator_id == "BIZ-001"
        assert operator.name == "Operator One"
        assert operator.user_id is None
        assert operator.is_active is True

    def test_operator_creation_with_all_fields(self):
        """Test creating Operator with all fields."""
        op_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        now = datetime.utcnow()

        operator = Operator(
            id=op_id,
            tenant_id=tenant_id,
            biztel_operator_id="BIZ-002",
            name="Operator Two",
            user_id=user_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        assert operator.id == op_id
        assert operator.tenant_id == tenant_id
        assert operator.biztel_operator_id == "BIZ-002"
        assert operator.user_id == user_id
        assert operator.is_active is True

    def test_operator_auto_generates_uuid(self):
        """Test that Operator auto-generates UUID."""
        operator = Operator(
            tenant_id=uuid.uuid4(),
            biztel_operator_id="BIZ-003",
            name="Operator Three",
        )

        assert operator.id is not None
        assert isinstance(operator.id, uuid.UUID)

    def test_operator_without_linked_user(self):
        """Test Operator without linked User account."""
        operator = Operator(
            tenant_id=uuid.uuid4(),
            biztel_operator_id="BIZ-004",
            name="Unlinked Operator",
        )

        assert operator.user_id is None

    def test_operator_inactive(self):
        """Test creating inactive operator."""
        operator = Operator(
            tenant_id=uuid.uuid4(),
            biztel_operator_id="BIZ-005",
            name="Inactive Op",
            is_active=False,
        )

        assert operator.is_active is False


class TestOperationFlowModel:
    """Tests for OperationFlow model."""

    def test_flow_creation_with_defaults(self):
        """Test creating OperationFlow with default values."""
        tenant_id = uuid.uuid4()
        flow = OperationFlow(
            tenant_id=tenant_id,
            name="Default Flow",
        )

        assert flow.tenant_id == tenant_id
        assert flow.name == "Default Flow"
        assert flow.classification_criteria is None
        assert flow.flow_definition == {}
        assert flow.is_active is True

    def test_flow_creation_with_all_fields(self):
        """Test creating OperationFlow with all fields."""
        flow_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.utcnow()
        definition = {
            "steps": [
                {"id": "1", "name": "Greeting"},
                {"id": "2", "name": "Resolution"},
            ]
        }

        flow = OperationFlow(
            id=flow_id,
            tenant_id=tenant_id,
            name="Complete Flow",
            classification_criteria="Product inquiry or complaint",
            flow_definition=definition,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        assert flow.id == flow_id
        assert flow.name == "Complete Flow"
        assert flow.classification_criteria == "Product inquiry or complaint"
        assert flow.flow_definition == definition
        assert len(flow.flow_definition["steps"]) == 2

    def test_flow_empty_definition(self):
        """Test OperationFlow with empty flow definition."""
        flow = OperationFlow(
            tenant_id=uuid.uuid4(),
            name="Empty Flow",
            flow_definition={},
        )

        assert flow.flow_definition == {}

    def test_flow_inactive(self):
        """Test creating inactive flow."""
        flow = OperationFlow(
            tenant_id=uuid.uuid4(),
            name="Inactive Flow",
            is_active=False,
        )

        assert flow.is_active is False


class TestAnalysisStatusEnum:
    """Tests for AnalysisStatus enum."""

    def test_status_values(self):
        """Test AnalysisStatus enum has expected values."""
        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.PROCESSING.value == "processing"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"

    def test_status_is_string_enum(self):
        """Test AnalysisStatus is a string enum."""
        assert isinstance(AnalysisStatus.PENDING.value, str)

    def test_status_member_count(self):
        """Test AnalysisStatus has exactly 4 members."""
        assert len(AnalysisStatus) == 4


class TestCallRecordModel:
    """Tests for CallRecord model."""

    def test_call_record_minimal(self):
        """Test creating CallRecord with minimal required fields."""
        tenant_id = uuid.uuid4()
        event_dt = datetime(2024, 1, 15, 10, 0, 0)
        call = CallRecord(
            tenant_id=tenant_id,
            event_datetime=event_dt,
        )

        assert call.tenant_id == tenant_id
        assert call.event_datetime == event_dt
        assert call.analysis_status == AnalysisStatus.PENDING
        assert call.biztel_id is None
        assert call.request_id is None
        assert call.operator_id is None
        assert call.operation_flow_id is None
        assert call.caller_number is None
        assert call.callee_number is None
        assert call.wait_time_seconds is None
        assert call.talk_time_seconds is None
        assert call.audio_file_path is None

    def test_call_record_with_all_fields(self):
        """Test creating CallRecord with all fields."""
        call_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        operator_id = uuid.uuid4()
        flow_id = uuid.uuid4()
        now = datetime.utcnow()

        call = CallRecord(
            id=call_id,
            tenant_id=tenant_id,
            biztel_id="BIZ-001",
            request_id="REQ-001",
            event_datetime=now,
            call_center_name="Support",
            call_center_extension="1001",
            business_label="Sales",
            operator_id=operator_id,
            operation_flow_id=flow_id,
            inquiry_category="Product Inquiry",
            event_type="COMPLETEAGENT",
            caller_number="03-1234-5678",
            callee_number="0120-123-456",
            wait_time_seconds=10,
            talk_time_seconds=180,
            audio_file_path="gs://bucket/audio/file.mp3",
            analysis_status=AnalysisStatus.COMPLETED,
        )

        assert call.id == call_id
        assert call.biztel_id == "BIZ-001"
        assert call.request_id == "REQ-001"
        assert call.call_center_name == "Support"
        assert call.operator_id == operator_id
        assert call.operation_flow_id == flow_id
        assert call.inquiry_category == "Product Inquiry"
        assert call.wait_time_seconds == 10
        assert call.talk_time_seconds == 180
        assert call.analysis_status == AnalysisStatus.COMPLETED

    def test_call_record_default_status(self):
        """Test CallRecord default analysis status is PENDING."""
        call = CallRecord(
            tenant_id=uuid.uuid4(),
            event_datetime=datetime.utcnow(),
        )

        assert call.analysis_status == AnalysisStatus.PENDING

    def test_call_record_status_transitions(self):
        """Test CallRecord analysis status can be set to all values."""
        call = CallRecord(
            tenant_id=uuid.uuid4(),
            event_datetime=datetime.utcnow(),
        )

        for status in AnalysisStatus:
            call.analysis_status = status
            assert call.analysis_status == status


class TestAnalysisResultModel:
    """Tests for AnalysisResult model."""

    def test_analysis_result_minimal(self):
        """Test creating AnalysisResult with minimal fields."""
        call_id = uuid.uuid4()
        result = AnalysisResult(call_record_id=call_id)

        assert result.call_record_id == call_id
        assert result.transcript is None
        assert result.flow_compliance is None
        assert result.compliance_details is None
        assert result.overall_score is None
        assert result.fillers_count is None
        assert result.silence_duration is None
        assert result.summary is None

    def test_analysis_result_with_all_fields(self):
        """Test creating AnalysisResult with all fields."""
        result_id = uuid.uuid4()
        call_id = uuid.uuid4()
        now = datetime.utcnow()

        result = AnalysisResult(
            id=result_id,
            call_record_id=call_id,
            transcript="Customer: Hello\nAgent: Hi, how can I help?",
            flow_compliance=True,
            compliance_details={"steps_completed": 4, "total": 4},
            overall_score=92.5,
            fillers_count=2,
            silence_duration=3.5,
            summary="Customer inquiry resolved successfully.",
            created_at=now,
            updated_at=now,
        )

        assert result.id == result_id
        assert result.call_record_id == call_id
        assert result.transcript is not None
        assert result.flow_compliance is True
        assert result.compliance_details["steps_completed"] == 4
        assert result.overall_score == 92.5
        assert result.fillers_count == 2
        assert result.silence_duration == 3.5
        assert "resolved" in result.summary

    def test_analysis_result_score_boundaries(self):
        """Test AnalysisResult score at boundaries."""
        result_min = AnalysisResult(
            call_record_id=uuid.uuid4(),
            overall_score=0.0,
        )
        assert result_min.overall_score == 0.0

        result_max = AnalysisResult(
            call_record_id=uuid.uuid4(),
            overall_score=100.0,
        )
        assert result_max.overall_score == 100.0

    def test_analysis_result_non_compliant(self):
        """Test AnalysisResult with non-compliant flow."""
        result = AnalysisResult(
            call_record_id=uuid.uuid4(),
            flow_compliance=False,
            compliance_details={"missing_steps": ["greeting", "closing"]},
            overall_score=45.0,
        )

        assert result.flow_compliance is False
        assert "missing_steps" in result.compliance_details


class TestEmotionDataModel:
    """Tests for EmotionData model."""

    def test_emotion_data_creation(self):
        """Test creating EmotionData with required fields."""
        analysis_id = uuid.uuid4()
        emotion = EmotionData(
            analysis_id=analysis_id,
            timestamp=10.5,
            emotion_type="joy",
            confidence=0.92,
        )

        assert emotion.analysis_id == analysis_id
        assert emotion.timestamp == 10.5
        assert emotion.emotion_type == "joy"
        assert emotion.confidence == 0.92
        assert emotion.audio_features is None

    def test_emotion_data_with_audio_features(self):
        """Test creating EmotionData with audio features."""
        emotion = EmotionData(
            analysis_id=uuid.uuid4(),
            timestamp=25.3,
            emotion_type="anger",
            confidence=0.78,
            audio_features={
                "pitch": 350.0,
                "energy": 0.8,
                "speech_rate": 4.2,
            },
        )

        assert emotion.audio_features is not None
        assert emotion.audio_features["pitch"] == 350.0
        assert emotion.audio_features["energy"] == 0.8

    def test_emotion_data_confidence_boundaries(self):
        """Test EmotionData confidence at boundaries."""
        emotion_min = EmotionData(
            analysis_id=uuid.uuid4(),
            timestamp=0.0,
            emotion_type="neutral",
            confidence=0.0,
        )
        assert emotion_min.confidence == 0.0

        emotion_max = EmotionData(
            analysis_id=uuid.uuid4(),
            timestamp=0.0,
            emotion_type="joy",
            confidence=1.0,
        )
        assert emotion_max.confidence == 1.0

    def test_emotion_data_various_types(self):
        """Test EmotionData with various emotion types."""
        emotion_types = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]
        analysis_id = uuid.uuid4()

        for emotion_type in emotion_types:
            emotion = EmotionData(
                analysis_id=analysis_id,
                timestamp=0.0,
                emotion_type=emotion_type,
                confidence=0.5,
            )
            assert emotion.emotion_type == emotion_type

    def test_emotion_data_auto_generates_uuid(self):
        """Test that EmotionData auto-generates UUID."""
        emotion = EmotionData(
            analysis_id=uuid.uuid4(),
            timestamp=5.0,
            emotion_type="neutral",
            confidence=0.5,
        )

        assert emotion.id is not None
        assert isinstance(emotion.id, uuid.UUID)
