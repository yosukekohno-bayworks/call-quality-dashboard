import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    call_record_id: uuid.UUID = Field(foreign_key="call_records.id", unique=True, index=True)
    transcript: str | None = Field(default=None)
    flow_compliance: bool | None = Field(default=None)
    compliance_details: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    overall_score: float | None = Field(default=None, ge=0, le=100)
    fillers_count: int | None = Field(default=None, ge=0)
    silence_duration: float | None = Field(default=None, ge=0)
    summary: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
