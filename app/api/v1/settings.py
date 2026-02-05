import uuid
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import AdminUser, QAUser, get_db
from app.models.call_record import AnalysisStatus, CallRecord
from app.models.operation_flow import OperationFlow
from app.models.operator import Operator
from app.models.tenant import Tenant
from app.schemas.biztel import (
    BiztelConnectionTestResponse,
    BiztelSettingsResponse,
    BiztelSettingsUpdate,
    BiztelSyncRequest,
    BiztelSyncResponse,
)
from app.services.biztel import (
    BiztelAuthError,
    BiztelClient,
    BiztelClientFactory,
    BiztelCredentials,
    BiztelEventType,
)
from app.services.storage import get_storage_service

router = APIRouter()


# ============================================================
# Operation Flows
# ============================================================


@router.get("/flows")
async def list_flows(
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all operation flows for the tenant."""
    result = await db.execute(
        select(OperationFlow)
        .where(OperationFlow.tenant_id == current_user.tenant_id)
        .order_by(OperationFlow.name)
    )
    flows = result.scalars().all()

    return {
        "items": [
            {
                "id": str(flow.id),
                "name": flow.name,
                "classification_criteria": flow.classification_criteria,
                "flow_definition": flow.flow_definition,
                "is_active": flow.is_active,
                "created_at": flow.created_at.isoformat(),
                "updated_at": flow.updated_at.isoformat(),
            }
            for flow in flows
        ]
    }


@router.post("/flows")
async def create_flow(
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    classification_criteria: str | None = None,
    flow_definition: dict[str, Any] | None = None,
):
    """Create a new operation flow."""
    flow = OperationFlow(
        tenant_id=current_user.tenant_id,
        name=name,
        classification_criteria=classification_criteria,
        flow_definition=flow_definition or {},
        is_active=True,
    )
    db.add(flow)
    await db.commit()
    await db.refresh(flow)

    return {
        "id": str(flow.id),
        "name": flow.name,
        "classification_criteria": flow.classification_criteria,
        "flow_definition": flow.flow_definition,
        "is_active": flow.is_active,
        "created_at": flow.created_at.isoformat(),
    }


@router.get("/flows/{flow_id}")
async def get_flow(
    flow_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific operation flow."""
    result = await db.execute(
        select(OperationFlow).where(
            OperationFlow.id == flow_id,
            OperationFlow.tenant_id == current_user.tenant_id,
        )
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation flow not found",
        )

    return {
        "id": str(flow.id),
        "name": flow.name,
        "classification_criteria": flow.classification_criteria,
        "flow_definition": flow.flow_definition,
        "is_active": flow.is_active,
        "created_at": flow.created_at.isoformat(),
        "updated_at": flow.updated_at.isoformat(),
    }


@router.put("/flows/{flow_id}")
async def update_flow(
    flow_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    classification_criteria: str | None = None,
    flow_definition: dict[str, Any] | None = None,
    is_active: bool | None = None,
):
    """Update an operation flow."""
    result = await db.execute(
        select(OperationFlow).where(
            OperationFlow.id == flow_id,
            OperationFlow.tenant_id == current_user.tenant_id,
        )
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation flow not found",
        )

    if name is not None:
        flow.name = name
    if classification_criteria is not None:
        flow.classification_criteria = classification_criteria
    if flow_definition is not None:
        flow.flow_definition = flow_definition
    if is_active is not None:
        flow.is_active = is_active

    flow.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(flow)

    return {
        "id": str(flow.id),
        "name": flow.name,
        "classification_criteria": flow.classification_criteria,
        "flow_definition": flow.flow_definition,
        "is_active": flow.is_active,
        "updated_at": flow.updated_at.isoformat(),
    }


@router.delete("/flows/{flow_id}")
async def delete_flow(
    flow_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an operation flow."""
    result = await db.execute(
        select(OperationFlow).where(
            OperationFlow.id == flow_id,
            OperationFlow.tenant_id == current_user.tenant_id,
        )
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation flow not found",
        )

    await db.delete(flow)
    await db.commit()

    return {"message": "Operation flow deleted"}


# ============================================================
# Analysis Prompts
# ============================================================


@router.get("/prompts")
async def list_prompts(
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    prompt_type: str | None = None,
):
    """List all analysis prompts for the tenant."""
    from app.models.analysis_prompt import AnalysisPrompt, PromptType

    query = select(AnalysisPrompt).where(
        AnalysisPrompt.tenant_id == current_user.tenant_id
    )

    if prompt_type:
        query = query.where(AnalysisPrompt.prompt_type == prompt_type)

    query = query.order_by(AnalysisPrompt.prompt_type, AnalysisPrompt.name)

    result = await db.execute(query)
    prompts = result.scalars().all()

    return {
        "items": [
            {
                "id": str(p.id),
                "prompt_type": p.prompt_type,
                "name": p.name,
                "description": p.description,
                "prompt_text": p.prompt_text,
                "is_active": p.is_active,
                "is_default": p.is_default,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in prompts
        ]
    }


@router.post("/prompts")
async def create_prompt(
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    prompt_type: str,
    name: str,
    prompt_text: str,
    description: str | None = None,
):
    """Create a new analysis prompt."""
    from app.models.analysis_prompt import AnalysisPrompt, PromptType

    prompt = AnalysisPrompt(
        tenant_id=current_user.tenant_id,
        prompt_type=PromptType(prompt_type),
        name=name,
        description=description,
        prompt_text=prompt_text,
        is_active=True,
        is_default=False,
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)

    return {
        "id": str(prompt.id),
        "prompt_type": prompt.prompt_type,
        "name": prompt.name,
        "description": prompt.description,
        "prompt_text": prompt.prompt_text,
        "is_active": prompt.is_active,
        "created_at": prompt.created_at.isoformat(),
    }


@router.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific analysis prompt."""
    from app.models.analysis_prompt import AnalysisPrompt

    result = await db.execute(
        select(AnalysisPrompt).where(
            AnalysisPrompt.id == prompt_id,
            AnalysisPrompt.tenant_id == current_user.tenant_id,
        )
    )
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )

    return {
        "id": str(prompt.id),
        "prompt_type": prompt.prompt_type,
        "name": prompt.name,
        "description": prompt.description,
        "prompt_text": prompt.prompt_text,
        "is_active": prompt.is_active,
        "is_default": prompt.is_default,
        "created_at": prompt.created_at.isoformat(),
        "updated_at": prompt.updated_at.isoformat(),
    }


@router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
    description: str | None = None,
    prompt_text: str | None = None,
    is_active: bool | None = None,
):
    """Update an analysis prompt."""
    from app.models.analysis_prompt import AnalysisPrompt

    result = await db.execute(
        select(AnalysisPrompt).where(
            AnalysisPrompt.id == prompt_id,
            AnalysisPrompt.tenant_id == current_user.tenant_id,
        )
    )
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )

    if name is not None:
        prompt.name = name
    if description is not None:
        prompt.description = description
    if prompt_text is not None:
        prompt.prompt_text = prompt_text
    if is_active is not None:
        prompt.is_active = is_active

    prompt.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prompt)

    return {
        "id": str(prompt.id),
        "prompt_type": prompt.prompt_type,
        "name": prompt.name,
        "description": prompt.description,
        "prompt_text": prompt.prompt_text,
        "is_active": prompt.is_active,
        "updated_at": prompt.updated_at.isoformat(),
    }


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(
    prompt_id: uuid.UUID,
    current_user: QAUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an analysis prompt."""
    from app.models.analysis_prompt import AnalysisPrompt

    result = await db.execute(
        select(AnalysisPrompt).where(
            AnalysisPrompt.id == prompt_id,
            AnalysisPrompt.tenant_id == current_user.tenant_id,
        )
    )
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )

    if prompt.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default prompt",
        )

    await db.delete(prompt)
    await db.commit()

    return {"message": "Prompt deleted"}


@router.post("/prompts/test")
async def test_prompt(
    current_user: QAUser,
    prompt_text: str,
    sample_transcript: str,
):
    """Test a prompt with sample transcript."""
    from app.services.llm import get_llm_service

    try:
        llm_service = get_llm_service()
        result = await llm_service._call_llm(
            system_prompt=prompt_text,
            user_prompt=f"## 通話内容:\n{sample_transcript}",
            max_tokens=1000,
        )
        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================
# Biztel Settings
# ============================================================


def _mask_api_key(api_key: str | None) -> str:
    """Mask API key, showing only last 4 characters."""
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "*" * len(api_key)
    return "*" * (len(api_key) - 4) + api_key[-4:]


@router.get("/biztel", response_model=BiztelSettingsResponse)
async def get_biztel_settings(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get Biztel API settings for the tenant."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return BiztelSettingsResponse(
        api_key_masked=_mask_api_key(tenant.biztel_api_key),
        base_url=tenant.biztel_base_url or "",
        is_configured=bool(tenant.biztel_api_key and tenant.biztel_base_url),
    )


@router.put("/biztel", response_model=BiztelSettingsResponse)
async def update_biztel_settings(
    request: BiztelSettingsUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update Biztel API settings for the tenant."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # TODO: Encrypt api_key and api_secret before storing
    tenant.biztel_api_key = request.api_key
    if request.api_secret:
        tenant.biztel_api_secret = request.api_secret
    tenant.biztel_base_url = request.base_url.rstrip("/")
    tenant.updated_at = datetime.utcnow()

    # Clear cached client to force recreation with new credentials
    BiztelClientFactory.clear_client(tenant.id)

    await db.commit()
    await db.refresh(tenant)

    return BiztelSettingsResponse(
        api_key_masked=_mask_api_key(tenant.biztel_api_key),
        base_url=tenant.biztel_base_url or "",
        is_configured=True,
    )


@router.post("/biztel/test", response_model=BiztelConnectionTestResponse)
async def test_biztel_connection(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Test Biztel API connection."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if not tenant.biztel_api_key or not tenant.biztel_base_url:
        return BiztelConnectionTestResponse(
            success=False,
            message="Biztel API credentials not configured",
        )

    try:
        credentials = BiztelCredentials(
            api_key=tenant.biztel_api_key,
            api_secret=tenant.biztel_api_secret or "",
            base_url=tenant.biztel_base_url,
        )
        client = BiztelClient(credentials)

        # Try to fetch recent history
        yesterday = datetime.utcnow() - timedelta(days=1)
        today = datetime.utcnow()
        records = await client.get_call_history(yesterday, today, limit=10)

        return BiztelConnectionTestResponse(
            success=True,
            message="Connection successful",
            records_found=len(records),
        )

    except BiztelAuthError:
        return BiztelConnectionTestResponse(
            success=False,
            message="Authentication failed. Please check your API key.",
        )
    except Exception as e:
        return BiztelConnectionTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
        )


@router.post("/biztel/sync", response_model=BiztelSyncResponse)
async def sync_biztel_data(
    request: BiztelSyncRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Sync call history from Biztel API.

    Downloads call records and recordings for the specified date range.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant or not tenant.biztel_api_key or not tenant.biztel_base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Biztel API credentials not configured",
        )

    credentials = BiztelCredentials(
        api_key=tenant.biztel_api_key,
        api_secret=tenant.biztel_api_secret or "",
        base_url=tenant.biztel_base_url,
    )
    client = BiztelClient(credentials)
    storage = get_storage_service()

    total_records = 0
    new_records = 0
    updated_records = 0
    recordings_downloaded = 0
    errors: list[str] = []

    # Cache operators
    operator_cache: dict[str, uuid.UUID] = {}

    try:
        # Fetch call history with pagination
        history_records = await client.get_call_history_paginated(
            start_date=request.start_date,
            end_date=request.end_date,
            queue_id=request.queue_id,
            events=[BiztelEventType.COMPLETECALLER, BiztelEventType.COMPLETEAGENT],
        )

        total_records = len(history_records)

        for record in history_records:
            try:
                # Check if record already exists
                existing = await db.execute(
                    select(CallRecord).where(
                        CallRecord.tenant_id == tenant.id,
                        CallRecord.request_id == record.request_id,
                    )
                )
                existing_call = existing.scalar_one_or_none()

                # Find or create operator
                operator_id = None
                if record.account_id:
                    if record.account_id not in operator_cache:
                        op_result = await db.execute(
                            select(Operator).where(
                                Operator.tenant_id == tenant.id,
                                Operator.biztel_operator_id == record.account_id,
                            )
                        )
                        operator = op_result.scalar_one_or_none()

                        if not operator and record.account_name:
                            operator = Operator(
                                tenant_id=tenant.id,
                                biztel_operator_id=record.account_id,
                                name=record.account_name,
                            )
                            db.add(operator)
                            await db.flush()

                        if operator:
                            operator_cache[record.account_id] = operator.id

                    operator_id = operator_cache.get(record.account_id)

                if existing_call:
                    # Update existing record
                    existing_call.operator_id = operator_id
                    existing_call.updated_at = datetime.utcnow()
                    updated_records += 1
                    call_record = existing_call
                else:
                    # Create new record
                    call_record = CallRecord(
                        tenant_id=tenant.id,
                        request_id=record.request_id,
                        event_datetime=record.start_time,
                        caller_number=record.caller_id,
                        callee_number=record.called_id,
                        wait_time_seconds=record.hold_time,
                        talk_time_seconds=record.call_time,
                        operator_id=operator_id,
                        call_center_name=record.queue_name,
                        call_center_extension=record.queue_exten,
                        business_label=record.business_name,
                        event_type=record.event,
                        analysis_status=AnalysisStatus.PENDING,
                    )
                    db.add(call_record)
                    await db.flush()
                    new_records += 1

                # Download recording if available and not already downloaded
                if record.has_recording and not call_record.audio_file_path:
                    try:
                        audio_content = await client.download_recording(record.request_id)
                        upload_result = await storage.upload_audio_file(
                            file_content=audio_content,
                            filename=f"{record.request_id}.mp3",
                            tenant_id=str(tenant.id),
                        )
                        call_record.audio_file_path = upload_result["blob_path"]
                        recordings_downloaded += 1
                    except Exception as e:
                        errors.append(f"Recording {record.request_id}: {str(e)}")

            except Exception as e:
                errors.append(f"Record {record.request_id}: {str(e)}")

        await db.commit()

    except Exception as e:
        errors.append(f"Sync failed: {str(e)}")

    return BiztelSyncResponse(
        total_records=total_records,
        new_records=new_records,
        updated_records=updated_records,
        recordings_downloaded=recordings_downloaded,
        errors=errors[:20],  # Limit errors returned
    )
