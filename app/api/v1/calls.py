import csv
import io
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import CurrentUser, get_db
from app.models.call_record import AnalysisStatus, CallRecord
from app.models.operator import Operator
from app.schemas.upload import (
    AudioUploadResponse,
    BulkUploadResponse,
    CSVUploadResponse,
    SignedUrlRequest,
    SignedUrlResponse,
)
from app.services.storage import get_storage_service

router = APIRouter()

# Allowed audio file types
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/mp4": [".m4a"],
    "audio/x-m4a": [".m4a"],
}

MAX_AUDIO_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def validate_audio_file(file: UploadFile) -> None:
    """Validate uploaded audio file."""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {list(ALLOWED_AUDIO_TYPES.keys())}",
        )


@router.get("")
async def list_calls(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    operator_id: uuid.UUID | None = None,
    status_filter: AnalysisStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """List call records with filtering and pagination."""
    query = select(CallRecord).where(CallRecord.tenant_id == current_user.tenant_id)

    if operator_id:
        query = query.where(CallRecord.operator_id == operator_id)
    if status_filter:
        query = query.where(CallRecord.analysis_status == status_filter)
    if date_from:
        query = query.where(CallRecord.event_datetime >= date_from)
    if date_to:
        query = query.where(CallRecord.event_datetime <= date_to)

    query = query.order_by(CallRecord.event_datetime.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    calls = result.scalars().all()

    return {
        "items": [
            {
                "id": str(call.id),
                "event_datetime": call.event_datetime.isoformat(),
                "operator_id": str(call.operator_id) if call.operator_id else None,
                "caller_number": call.caller_number,
                "callee_number": call.callee_number,
                "talk_time_seconds": call.talk_time_seconds,
                "analysis_status": call.analysis_status,
                "inquiry_category": call.inquiry_category,
            }
            for call in calls
        ],
        "skip": skip,
        "limit": limit,
    }


@router.get("/{call_id}")
async def get_call(
    call_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific call record."""
    result = await db.execute(
        select(CallRecord).where(
            CallRecord.id == call_id,
            CallRecord.tenant_id == current_user.tenant_id,
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found",
        )

    # Generate signed URL if audio file exists
    signed_url = None
    if call.audio_file_path:
        storage = get_storage_service()
        signed_url = storage.generate_signed_url(call.audio_file_path)

    return {
        "id": str(call.id),
        "biztel_id": call.biztel_id,
        "request_id": call.request_id,
        "event_datetime": call.event_datetime.isoformat(),
        "call_center_name": call.call_center_name,
        "call_center_extension": call.call_center_extension,
        "business_label": call.business_label,
        "operator_id": str(call.operator_id) if call.operator_id else None,
        "operation_flow_id": str(call.operation_flow_id) if call.operation_flow_id else None,
        "inquiry_category": call.inquiry_category,
        "event_type": call.event_type,
        "caller_number": call.caller_number,
        "callee_number": call.callee_number,
        "wait_time_seconds": call.wait_time_seconds,
        "talk_time_seconds": call.talk_time_seconds,
        "audio_file_path": call.audio_file_path,
        "audio_signed_url": signed_url,
        "analysis_status": call.analysis_status,
        "created_at": call.created_at.isoformat(),
    }


@router.post("/upload/audio", response_model=AudioUploadResponse)
async def upload_audio(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    event_datetime: datetime = Query(..., description="Call event datetime"),
    operator_name: str | None = Query(None, description="Operator name"),
    caller_number: str | None = Query(None),
    callee_number: str | None = Query(None),
    talk_time_seconds: int | None = Query(None),
):
    """
    Upload a single audio file with metadata.

    Creates a CallRecord and uploads the audio to GCS.
    """
    validate_audio_file(file)

    # Read file content
    content = await file.read()
    if len(content) > MAX_AUDIO_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_AUDIO_FILE_SIZE // (1024*1024)}MB",
        )

    # Find or create operator if name provided
    operator_id = None
    if operator_name:
        result = await db.execute(
            select(Operator).where(
                Operator.tenant_id == current_user.tenant_id,
                Operator.name == operator_name,
            )
        )
        operator = result.scalar_one_or_none()
        if operator:
            operator_id = operator.id

    # Upload to GCS
    storage = get_storage_service()
    upload_result = await storage.upload_audio_file(
        file_content=content,
        filename=file.filename or "audio.mp3",
        tenant_id=str(current_user.tenant_id),
        content_type=file.content_type or "audio/mpeg",
    )

    # Create call record
    call_record = CallRecord(
        tenant_id=current_user.tenant_id,
        event_datetime=event_datetime,
        operator_id=operator_id,
        caller_number=caller_number,
        callee_number=callee_number,
        talk_time_seconds=talk_time_seconds,
        audio_file_path=upload_result["blob_path"],
        analysis_status=AnalysisStatus.PENDING,
    )
    db.add(call_record)
    await db.commit()
    await db.refresh(call_record)

    return AudioUploadResponse(
        call_record_id=str(call_record.id),
        blob_path=upload_result["blob_path"],
        signed_url=upload_result["signed_url"],
        expires_at=upload_result["expires_at"],
    )


@router.post("/upload/csv", response_model=CSVUploadResponse)
async def upload_csv_metadata(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """
    Upload CSV file with call metadata.

    Expected columns:
    - event_datetime (required): ISO format datetime
    - operator_name: Operator name
    - caller_number: Caller phone number
    - callee_number: Callee phone number
    - call_center_name: Call center name
    - business_label: Business label
    - wait_time_seconds: Wait time in seconds
    - talk_time_seconds: Talk time in seconds
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )

    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text_content = content.decode("shift_jis")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode CSV file. Please use UTF-8 or Shift-JIS encoding.",
            )

    reader = csv.DictReader(io.StringIO(text_content))

    created_count = 0
    skipped_count = 0
    errors = []

    # Cache operators by name
    operator_cache: dict[str, uuid.UUID | None] = {}

    for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
        try:
            # Parse event_datetime
            event_datetime_str = row.get("event_datetime", "").strip()
            if not event_datetime_str:
                errors.append(f"Row {row_num}: event_datetime is required")
                skipped_count += 1
                continue

            try:
                event_datetime = datetime.fromisoformat(event_datetime_str)
            except ValueError:
                errors.append(f"Row {row_num}: Invalid datetime format")
                skipped_count += 1
                continue

            # Find operator
            operator_id = None
            operator_name = row.get("operator_name", "").strip()
            if operator_name:
                if operator_name not in operator_cache:
                    result = await db.execute(
                        select(Operator).where(
                            Operator.tenant_id == current_user.tenant_id,
                            Operator.name == operator_name,
                        )
                    )
                    operator = result.scalar_one_or_none()
                    operator_cache[operator_name] = operator.id if operator else None
                operator_id = operator_cache[operator_name]

            # Parse optional integers
            wait_time = None
            talk_time = None
            if row.get("wait_time_seconds"):
                try:
                    wait_time = int(row["wait_time_seconds"])
                except ValueError:
                    pass
            if row.get("talk_time_seconds"):
                try:
                    talk_time = int(row["talk_time_seconds"])
                except ValueError:
                    pass

            # Create call record
            call_record = CallRecord(
                tenant_id=current_user.tenant_id,
                event_datetime=event_datetime,
                operator_id=operator_id,
                caller_number=row.get("caller_number", "").strip() or None,
                callee_number=row.get("callee_number", "").strip() or None,
                call_center_name=row.get("call_center_name", "").strip() or None,
                call_center_extension=row.get("call_center_extension", "").strip() or None,
                business_label=row.get("business_label", "").strip() or None,
                wait_time_seconds=wait_time,
                talk_time_seconds=talk_time,
                analysis_status=AnalysisStatus.PENDING,
            )
            db.add(call_record)
            created_count += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            skipped_count += 1

    await db.commit()

    return CSVUploadResponse(
        total_rows=created_count + skipped_count,
        created_count=created_count,
        skipped_count=skipped_count,
        errors=errors[:10],  # Limit errors returned
    )


@router.post("/upload/bulk", response_model=BulkUploadResponse)
async def upload_bulk(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    files: list[UploadFile] = File(...),
):
    """
    Upload multiple audio files at once.

    Each file creates a new CallRecord with the current datetime.
    """
    uploaded_files = 0
    created_records = 0
    errors = []

    storage = get_storage_service()

    for file in files:
        try:
            # Validate file type
            if file.content_type not in ALLOWED_AUDIO_TYPES:
                errors.append(f"{file.filename}: Invalid file type")
                continue

            content = await file.read()
            if len(content) > MAX_AUDIO_FILE_SIZE:
                errors.append(f"{file.filename}: File too large")
                continue

            # Upload to GCS
            upload_result = await storage.upload_audio_file(
                file_content=content,
                filename=file.filename or "audio.mp3",
                tenant_id=str(current_user.tenant_id),
                content_type=file.content_type or "audio/mpeg",
            )
            uploaded_files += 1

            # Create call record
            call_record = CallRecord(
                tenant_id=current_user.tenant_id,
                event_datetime=datetime.utcnow(),
                audio_file_path=upload_result["blob_path"],
                analysis_status=AnalysisStatus.PENDING,
            )
            db.add(call_record)
            created_records += 1

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    await db.commit()

    return BulkUploadResponse(
        uploaded_files=uploaded_files,
        created_records=created_records,
        errors=errors,
    )


@router.post("/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    request: SignedUrlRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate a signed URL for accessing an audio file."""
    # Verify the file belongs to user's tenant
    result = await db.execute(
        select(CallRecord).where(
            CallRecord.audio_file_path == request.blob_path,
            CallRecord.tenant_id == current_user.tenant_id,
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied",
        )

    storage = get_storage_service()
    signed_url = storage.generate_signed_url(
        request.blob_path,
        expiration_minutes=request.expiration_minutes,
    )

    return SignedUrlResponse(
        signed_url=signed_url,
        expires_in_minutes=request.expiration_minutes,
    )


@router.get("/{call_id}/analysis")
async def get_call_analysis(
    call_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get analysis result for a call record."""
    from app.models.analysis_result import AnalysisResult

    result = await db.execute(
        select(CallRecord).where(
            CallRecord.id == call_id,
            CallRecord.tenant_id == current_user.tenant_id,
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found",
        )

    # Get analysis result
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.call_record_id == call_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        return {
            "call_id": str(call_id),
            "status": call.analysis_status,
            "analysis": None,
        }

    return {
        "call_id": str(call_id),
        "status": call.analysis_status,
        "analysis": {
            "id": str(analysis.id),
            "transcript": analysis.transcript,
            "flow_compliance": analysis.flow_compliance,
            "compliance_details": analysis.compliance_details,
            "overall_score": analysis.overall_score,
            "fillers_count": analysis.fillers_count,
            "silence_duration": analysis.silence_duration,
            "summary": analysis.summary,
            "created_at": analysis.created_at.isoformat(),
        },
    }


@router.post("/{call_id}/reanalyze")
async def reanalyze_call(
    call_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger re-analysis for a call record."""
    result = await db.execute(
        select(CallRecord).where(
            CallRecord.id == call_id,
            CallRecord.tenant_id == current_user.tenant_id,
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found",
        )

    if not call.audio_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file associated with this call",
        )

    # Reset status to pending
    call.analysis_status = AnalysisStatus.PENDING
    await db.commit()

    # TODO: Trigger Celery task for re-analysis

    return {
        "message": "Re-analysis queued",
        "call_id": str(call_id),
        "status": call.analysis_status,
    }
