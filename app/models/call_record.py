import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CallRecord(SQLModel, table=True):
    __tablename__ = "call_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenants.id", index=True)
    biztel_id: str | None = Field(default=None, max_length=255, index=True)
    request_id: str | None = Field(default=None, max_length=255, index=True)
    event_datetime: datetime = Field(index=True)
    call_center_name: str | None = Field(default=None, max_length=255)
    call_center_extension: str | None = Field(default=None, max_length=50)
    business_label: str | None = Field(default=None, max_length=255)
    operator_id: uuid.UUID | None = Field(default=None, foreign_key="operators.id", index=True)
    operation_flow_id: uuid.UUID | None = Field(
        default=None, foreign_key="operation_flows.id", index=True
    )
    inquiry_category: str | None = Field(default=None, max_length=255)
    event_type: str | None = Field(default=None, max_length=50)
    caller_number: str | None = Field(default=None, max_length=50)
    callee_number: str | None = Field(default=None, max_length=50)
    wait_time_seconds: int | None = Field(default=None)
    talk_time_seconds: int | None = Field(default=None)
    audio_file_path: str | None = Field(default=None, max_length=512)
    analysis_status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
