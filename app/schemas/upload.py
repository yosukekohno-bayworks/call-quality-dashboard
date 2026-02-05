from datetime import datetime
from pydantic import BaseModel, Field


class AudioUploadResponse(BaseModel):
    """Response for audio file upload."""
    call_record_id: str
    blob_path: str
    signed_url: str
    expires_at: str


class CSVUploadRow(BaseModel):
    """Single row from CSV metadata upload."""
    event_datetime: datetime
    operator_name: str | None = None
    operator_id: str | None = None
    caller_number: str | None = None
    callee_number: str | None = None
    call_center_name: str | None = None
    call_center_extension: str | None = None
    business_label: str | None = None
    wait_time_seconds: int | None = None
    talk_time_seconds: int | None = None
    audio_filename: str | None = None  # To match with uploaded audio files


class CSVUploadRequest(BaseModel):
    """Request for CSV metadata upload with audio file mapping."""
    rows: list[CSVUploadRow]


class CSVUploadResponse(BaseModel):
    """Response for CSV metadata upload."""
    total_rows: int
    created_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)


class BulkUploadResponse(BaseModel):
    """Response for bulk upload (audio + metadata)."""
    uploaded_files: int
    created_records: int
    errors: list[str] = Field(default_factory=list)


class SignedUrlRequest(BaseModel):
    """Request for generating a signed URL."""
    blob_path: str
    expiration_minutes: int = 60


class SignedUrlResponse(BaseModel):
    """Response with signed URL."""
    signed_url: str
    expires_in_minutes: int
