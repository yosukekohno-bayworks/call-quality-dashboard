from datetime import datetime

from pydantic import BaseModel, Field

from app.models.analysis_prompt import PromptType


class PromptCreate(BaseModel):
    """Request to create a new prompt."""
    prompt_type: PromptType
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    prompt_text: str = Field(..., min_length=1)
    is_active: bool = True


class PromptUpdate(BaseModel):
    """Request to update a prompt."""
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    prompt_text: str | None = None
    is_active: bool | None = None


class PromptResponse(BaseModel):
    """Response with prompt details."""
    id: str
    prompt_type: PromptType
    name: str
    description: str | None
    prompt_text: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptTestRequest(BaseModel):
    """Request to test a prompt with sample data."""
    prompt_text: str
    sample_transcript: str


class PromptTestResponse(BaseModel):
    """Response from prompt test."""
    success: bool
    result: str | None = None
    error: str | None = None
