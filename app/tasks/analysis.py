import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any

from celery import group, shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.celery_app import celery_app
from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.call_record import AnalysisStatus, CallRecord
from app.models.emotion_data import EmotionData
from app.models.operation_flow import OperationFlow
from app.models.tenant import Tenant
from app.services.biztel import (
    BiztelClient,
    BiztelCredentials,
    BiztelEventType,
)
from app.services.hume import get_hume_service
from app.services.llm import get_llm_service
from app.services.storage import get_storage_service
from app.services.whisper import get_whisper_service


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session for Celery tasks."""
    engine = create_async_engine(settings.DATABASE_URL)
    return async_sessionmaker(engine, expire_on_commit=False)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Create new loop if current one is running
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def process_single_call(self, call_record_id: str) -> dict[str, Any]:
    """
    Process a single call record: transcription, emotion analysis, LLM analysis.

    Args:
        call_record_id: UUID of the call record to process

    Returns:
        Dict with analysis results
    """
    return run_async(_process_single_call_async(self, call_record_id))


async def _process_single_call_async(task, call_record_id: str) -> dict[str, Any]:
    """Async implementation of process_single_call."""
    async_session = get_async_session()

    async with async_session() as db:
        # Get call record
        result = await db.execute(
            select(CallRecord).where(CallRecord.id == call_record_id)
        )
        call = result.scalar_one_or_none()

        if not call:
            return {"error": "Call record not found"}

        if not call.audio_file_path:
            return {"error": "No audio file"}

        try:
            # Update status to processing
            call.analysis_status = AnalysisStatus.PROCESSING
            await db.commit()

            # Download audio from GCS
            storage = get_storage_service()
            audio_content = await storage.download_file(call.audio_file_path)

            # Run Whisper transcription and Hume emotion analysis in parallel
            whisper_service = get_whisper_service()
            hume_service = get_hume_service()

            transcription_task = whisper_service.transcribe(
                audio_content,
                filename=call.audio_file_path.split("/")[-1],
                language="ja",
            )
            emotion_task = hume_service.analyze_voice_emotions(
                audio_content,
                filename=call.audio_file_path.split("/")[-1],
            )

            transcription_result, emotion_result = await asyncio.gather(
                transcription_task,
                emotion_task,
                return_exceptions=True,
            )

            # Handle transcription errors
            if isinstance(transcription_result, Exception):
                raise transcription_result
            transcript = transcription_result.text

            # Get available flows for this tenant
            flows_result = await db.execute(
                select(OperationFlow).where(
                    OperationFlow.tenant_id == call.tenant_id,
                    OperationFlow.is_active == True,
                )
            )
            flows = flows_result.scalars().all()
            available_flows = [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "classification_criteria": f.classification_criteria,
                    "flow_definition": f.flow_definition,
                }
                for f in flows
            ]

            # Run LLM analysis
            llm_service = get_llm_service()
            llm_result = await llm_service.full_analysis(
                transcript=transcript,
                available_flows=available_flows if available_flows else None,
            )

            # Update call record with classified flow
            flow_classification = llm_result.get("flow_classification", {})
            if flow_classification.get("flow_id"):
                call.operation_flow_id = uuid.UUID(flow_classification["flow_id"])

            summary_data = llm_result.get("summary", {})
            call.inquiry_category = summary_data.get("inquiry_category")

            # Create or update analysis result
            existing_analysis = await db.execute(
                select(AnalysisResult).where(AnalysisResult.call_record_id == call.id)
            )
            analysis = existing_analysis.scalar_one_or_none()

            quality_score = llm_result.get("quality_score", {})
            compliance = llm_result.get("flow_compliance", {})
            filler = llm_result.get("filler_analysis", {})

            if analysis:
                analysis.transcript = transcript
                analysis.flow_compliance = compliance.get("is_compliant")
                analysis.compliance_details = compliance
                analysis.overall_score = quality_score.get("overall_score", 0)
                analysis.fillers_count = filler.get("filler_count", 0)
                analysis.silence_duration = filler.get("silence_duration", 0)
                analysis.summary = summary_data.get("summary")
                analysis.updated_at = datetime.utcnow()
            else:
                analysis = AnalysisResult(
                    call_record_id=call.id,
                    transcript=transcript,
                    flow_compliance=compliance.get("is_compliant"),
                    compliance_details=compliance,
                    overall_score=quality_score.get("overall_score", 0),
                    fillers_count=filler.get("filler_count", 0),
                    silence_duration=filler.get("silence_duration", 0),
                    summary=summary_data.get("summary"),
                )
                db.add(analysis)
                await db.flush()

            # Save emotion data if available
            if not isinstance(emotion_result, Exception):
                # Delete existing emotion data
                await db.execute(
                    select(EmotionData).where(EmotionData.analysis_id == analysis.id)
                )
                # Note: In production, use DELETE statement

                for prediction in emotion_result.predictions:
                    emotion_data = EmotionData(
                        analysis_id=analysis.id,
                        timestamp=prediction.start_time,
                        emotion_type=prediction.dominant_emotion,
                        confidence=prediction.dominant_score,
                        audio_features={
                            "emotions": {e.emotion: e.score for e in prediction.emotions}
                        },
                    )
                    db.add(emotion_data)

            # Update call status
            call.analysis_status = AnalysisStatus.COMPLETED
            call.updated_at = datetime.utcnow()

            await db.commit()

            return {
                "call_record_id": call_record_id,
                "status": "completed",
                "overall_score": quality_score.get("overall_score"),
                "inquiry_category": summary_data.get("inquiry_category"),
            }

        except Exception as e:
            # Update status to failed
            call.analysis_status = AnalysisStatus.FAILED
            await db.commit()

            # Retry on failure
            raise task.retry(exc=e, countdown=60)


@celery_app.task(bind=True)
def process_pending_calls(self, tenant_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    """
    Process all pending call records.

    Args:
        tenant_id: Optional tenant ID to filter calls
        limit: Maximum number of calls to process

    Returns:
        Dict with processing results
    """
    return run_async(_process_pending_calls_async(tenant_id, limit))


async def _process_pending_calls_async(tenant_id: str | None, limit: int) -> dict[str, Any]:
    """Async implementation of process_pending_calls."""
    async_session = get_async_session()

    async with async_session() as db:
        query = select(CallRecord).where(
            CallRecord.analysis_status == AnalysisStatus.PENDING,
            CallRecord.audio_file_path.isnot(None),
        )

        if tenant_id:
            query = query.where(CallRecord.tenant_id == tenant_id)

        query = query.limit(limit)

        result = await db.execute(query)
        calls = result.scalars().all()

        # Create tasks for each call
        tasks = [process_single_call.s(str(call.id)) for call in calls]

        if tasks:
            # Execute tasks in parallel with Celery group
            job = group(tasks)
            result = job.apply_async()

            return {
                "queued_count": len(tasks),
                "task_group_id": str(result.id),
            }

        return {"queued_count": 0}


@celery_app.task(bind=True)
def daily_biztel_sync(self, tenant_id: str | None = None) -> dict[str, Any]:
    """
    Daily sync task for Biztel data.

    Fetches yesterday's call history and downloads recordings.
    Should be triggered by Cloud Scheduler at 3:00 AM.
    """
    return run_async(_daily_biztel_sync_async(tenant_id))


async def _daily_biztel_sync_async(tenant_id: str | None) -> dict[str, Any]:
    """Async implementation of daily_biztel_sync."""
    async_session = get_async_session()
    results = []

    async with async_session() as db:
        # Get all tenants with Biztel configured
        query = select(Tenant).where(
            Tenant.biztel_api_key.isnot(None),
            Tenant.biztel_base_url.isnot(None),
            Tenant.is_active == True,
        )

        if tenant_id:
            query = query.where(Tenant.id == tenant_id)

        result = await db.execute(query)
        tenants = result.scalars().all()

        for tenant in tenants:
            try:
                credentials = BiztelCredentials(
                    api_key=tenant.biztel_api_key,
                    api_secret=tenant.biztel_api_secret or "",
                    base_url=tenant.biztel_base_url,
                )
                client = BiztelClient(credentials)

                # Fetch yesterday's data
                yesterday = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
                today = yesterday + timedelta(days=1)

                records = await client.get_call_history_paginated(
                    start_date=yesterday,
                    end_date=today,
                    events=[BiztelEventType.COMPLETECALLER, BiztelEventType.COMPLETEAGENT],
                )

                results.append({
                    "tenant_id": str(tenant.id),
                    "records_fetched": len(records),
                    "status": "success",
                })

                # Queue processing tasks for new records
                process_pending_calls.delay(str(tenant.id), limit=1000)

            except Exception as e:
                results.append({
                    "tenant_id": str(tenant.id),
                    "error": str(e),
                    "status": "failed",
                })

    return {
        "tenants_processed": len(results),
        "results": results,
    }


@celery_app.task
def cleanup_expired_files() -> dict[str, Any]:
    """
    Cleanup expired files from GCS.

    Removes audio files that have passed their TTL.
    """
    return run_async(_cleanup_expired_files_async())


async def _cleanup_expired_files_async() -> dict[str, Any]:
    """Async implementation of cleanup_expired_files."""
    storage = get_storage_service()
    deleted_count = await storage.cleanup_expired_files()

    return {
        "deleted_count": deleted_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery_app.task
def retry_failed_analyses(tenant_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    Retry failed analysis tasks.

    Args:
        tenant_id: Optional tenant ID to filter
        limit: Maximum number of retries

    Returns:
        Dict with retry results
    """
    return run_async(_retry_failed_analyses_async(tenant_id, limit))


async def _retry_failed_analyses_async(tenant_id: str | None, limit: int) -> dict[str, Any]:
    """Async implementation of retry_failed_analyses."""
    async_session = get_async_session()

    async with async_session() as db:
        query = select(CallRecord).where(
            CallRecord.analysis_status == AnalysisStatus.FAILED,
            CallRecord.audio_file_path.isnot(None),
        )

        if tenant_id:
            query = query.where(CallRecord.tenant_id == tenant_id)

        query = query.limit(limit)

        result = await db.execute(query)
        calls = result.scalars().all()

        # Reset status to pending
        for call in calls:
            call.analysis_status = AnalysisStatus.PENDING

        await db.commit()

        # Queue for reprocessing
        tasks = [process_single_call.s(str(call.id)) for call in calls]

        if tasks:
            job = group(tasks)
            result = job.apply_async()

            return {
                "retried_count": len(tasks),
                "task_group_id": str(result.id),
            }

        return {"retried_count": 0}
