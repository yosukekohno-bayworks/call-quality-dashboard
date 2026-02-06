"""
API tests for calls endpoints.

Tests the fully implemented call record endpoints with authentication,
filtering, pagination, and CRUD operations.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_record import AnalysisStatus, CallRecord
from app.models.analysis_result import AnalysisResult
from app.models.user import User


class TestListCallsEndpoint:
    """Tests for GET /api/calls endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.get("/api/calls")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_calls_empty(self, client: AsyncClient, auth_headers: dict):
        """Test list calls returns empty items when no records exist."""
        response = await client.get("/api/calls", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 50

    @pytest.mark.asyncio
    async def test_list_calls_with_record(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test list calls returns existing records."""
        response = await client.get("/api/calls", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_call_record.id)
        assert data["items"][0]["caller_number"] == "03-1234-5678"
        assert data["items"][0]["callee_number"] == "0120-123-456"
        assert data["items"][0]["talk_time_seconds"] == 300

    @pytest.mark.asyncio
    async def test_list_calls_pagination(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test list calls respects pagination parameters."""
        response = await client.get(
            "/api/calls", headers=auth_headers, params={"skip": 0, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_calls_skip_past_results(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test list calls returns empty when skip exceeds total records."""
        response = await client.get(
            "/api/calls", headers=auth_headers, params={"skip": 100}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_list_calls_filter_by_status_matching(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test list calls filtered by matching analysis status."""
        response = await client.get(
            "/api/calls",
            headers=auth_headers,
            params={"status_filter": "completed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_list_calls_filter_by_status_non_matching(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test list calls filtered by non-matching status returns empty."""
        response = await client.get(
            "/api/calls",
            headers=auth_headers,
            params={"status_filter": "pending"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_list_calls_operator_can_access(
        self,
        client: AsyncClient,
        operator_auth_headers: dict,
        test_call_record: CallRecord,
    ):
        """Test that operator user in same tenant can list calls."""
        response = await client.get("/api/calls", headers=operator_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1


class TestGetCallEndpoint:
    """Tests for GET /api/calls/{call_id} endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        call_id = str(uuid.uuid4())
        response = await client.get(f"/api/calls/{call_id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_call_returns_detail(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test get call returns full call detail."""
        response = await client.get(
            f"/api/calls/{test_call_record.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_call_record.id)
        assert data["biztel_id"] == "BIZTEL-CALL-001"
        assert data["request_id"] == "REQ-001"
        assert data["caller_number"] == "03-1234-5678"
        assert data["callee_number"] == "0120-123-456"
        assert data["talk_time_seconds"] == 300
        assert data["wait_time_seconds"] == 15
        assert data["call_center_name"] == "Support Center"
        assert data["business_label"] == "Product Support"
        assert data["event_type"] == "COMPLETEAGENT"
        assert data["audio_file_path"] is None
        assert data["audio_signed_url"] is None

    @pytest.mark.asyncio
    async def test_get_call_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get call returns 404 for non-existent record."""
        call_id = str(uuid.uuid4())
        response = await client.get(f"/api/calls/{call_id}", headers=auth_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Call record not found"

    @pytest.mark.asyncio
    async def test_get_call_invalid_uuid(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get call returns 422 for invalid UUID format."""
        response = await client.get("/api/calls/not-a-uuid", headers=auth_headers)
        assert response.status_code == 422


class TestGetCallAnalysisEndpoint:
    """Tests for GET /api/calls/{call_id}/analysis endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        call_id = str(uuid.uuid4())
        response = await client.get(f"/api/calls/{call_id}/analysis")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_analysis_with_result(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_call_record: CallRecord,
        test_analysis_result: AnalysisResult,
    ):
        """Test get analysis returns analysis data when available."""
        response = await client.get(
            f"/api/calls/{test_call_record.id}/analysis", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["call_id"] == str(test_call_record.id)
        assert data["analysis"] is not None
        assert data["analysis"]["overall_score"] == 85.5
        assert data["analysis"]["flow_compliance"] is True
        assert data["analysis"]["fillers_count"] == 3
        assert data["analysis"]["silence_duration"] == 5.2
        assert "transcript" in data["analysis"]
        assert "summary" in data["analysis"]

    @pytest.mark.asyncio
    async def test_get_analysis_without_result(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_call_record: CallRecord,
    ):
        """Test get analysis returns null when no analysis exists."""
        response = await client.get(
            f"/api/calls/{test_call_record.id}/analysis", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["call_id"] == str(test_call_record.id)
        assert data["analysis"] is None

    @pytest.mark.asyncio
    async def test_get_analysis_call_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get analysis returns 404 for non-existent call."""
        call_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/calls/{call_id}/analysis", headers=auth_headers
        )
        assert response.status_code == 404


class TestReanalyzeCallEndpoint:
    """Tests for POST /api/calls/{call_id}/reanalyze endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        call_id = str(uuid.uuid4())
        response = await client.post(f"/api/calls/{call_id}/reanalyze")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_reanalyze_call_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test reanalyze returns 404 for non-existent call."""
        call_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/calls/{call_id}/reanalyze", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reanalyze_call_no_audio(
        self, client: AsyncClient, auth_headers: dict, test_call_record: CallRecord
    ):
        """Test reanalyze returns 400 when no audio file is associated."""
        response = await client.post(
            f"/api/calls/{test_call_record.id}/reanalyze", headers=auth_headers
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "No audio file associated with this call"

    @pytest.mark.asyncio
    async def test_reanalyze_call_with_audio(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_call_record: CallRecord,
        db_session: AsyncSession,
    ):
        """Test reanalyze succeeds when audio file exists."""
        test_call_record.audio_file_path = "tenants/test/audio/test.mp3"
        test_call_record.analysis_status = AnalysisStatus.COMPLETED
        await db_session.commit()
        await db_session.refresh(test_call_record)

        response = await client.post(
            f"/api/calls/{test_call_record.id}/reanalyze", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Re-analysis queued"
        assert data["call_id"] == str(test_call_record.id)


class TestUploadEndpoints:
    """Tests for upload endpoints (auth checks only, GCS not available in tests)."""

    @pytest.mark.asyncio
    async def test_upload_audio_unauthenticated(self, client: AsyncClient):
        """Test that audio upload requires authentication."""
        response = await client.post("/api/calls/upload/audio")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_csv_unauthenticated(self, client: AsyncClient):
        """Test that CSV upload requires authentication."""
        response = await client.post("/api/calls/upload/csv")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_bulk_unauthenticated(self, client: AsyncClient):
        """Test that bulk upload requires authentication."""
        response = await client.post("/api/calls/upload/bulk")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_signed_url_unauthenticated(self, client: AsyncClient):
        """Test that signed URL endpoint requires authentication."""
        response = await client.post("/api/calls/signed-url")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_old_upload_endpoint_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that old /api/calls/upload endpoint does not exist."""
        response = await client.post("/api/calls/upload", headers=auth_headers)
        assert response.status_code == 405 or response.status_code == 404
