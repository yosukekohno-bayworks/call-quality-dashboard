import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class EmotionData(SQLModel, table=True):
    __tablename__ = "emotion_data"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    analysis_id: uuid.UUID = Field(foreign_key="analysis_results.id", index=True)
    timestamp: float = Field(ge=0)
    emotion_type: str = Field(max_length=50)
    confidence: float = Field(ge=0, le=1)
    audio_features: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
