import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class PromptType(str, Enum):
    """Types of analysis prompts."""
    QUALITY_SCORE = "quality_score"  # 品質スコア評価
    SUMMARY = "summary"  # 通話要約
    EMOTION = "emotion"  # 感情分析
    FLOW_CLASSIFICATION = "flow_classification"  # フロー分類
    FLOW_COMPLIANCE = "flow_compliance"  # フロー遵守チェック
    CUSTOM = "custom"  # カスタム


class AnalysisPrompt(SQLModel, table=True):
    __tablename__ = "analysis_prompts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenants.id", index=True)
    prompt_type: PromptType = Field(index=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    prompt_text: str = Field(default="")
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
