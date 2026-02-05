from datetime import datetime
from pydantic import BaseModel, Field


class BiztelSettingsUpdate(BaseModel):
    """Request to update Biztel API settings."""
    api_key: str = Field(..., min_length=1, description="Biztel API key")
    api_secret: str | None = Field(None, description="Biztel API secret (optional)")
    base_url: str = Field(..., min_length=1, description="Biztel API base URL (e.g., https://example.biztel.jp:8000)")


class BiztelSettingsResponse(BaseModel):
    """Response with Biztel API settings (secrets masked)."""
    api_key_masked: str  # Show only last 4 characters
    base_url: str
    is_configured: bool
    last_sync_at: datetime | None = None


class BiztelConnectionTestResponse(BaseModel):
    """Response from connection test."""
    success: bool
    message: str
    records_found: int | None = None


class BiztelSyncRequest(BaseModel):
    """Request to sync call history from Biztel."""
    start_date: datetime
    end_date: datetime
    queue_id: int | None = None


class BiztelSyncResponse(BaseModel):
    """Response from sync operation."""
    total_records: int
    new_records: int
    updated_records: int
    recordings_downloaded: int
    errors: list[str] = Field(default_factory=list)
