"""
API tests for calls endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestListCallsEndpoint:
    """Tests for GET /api/calls endpoint."""

    @pytest.mark.asyncio
    async def test_list_calls_returns_message(self, client: AsyncClient):
        """Test list calls endpoint returns not implemented message."""
        response = await client.get("/api/calls")

        assert response.status_code == 200
        assert response.json()["message"] == "List calls - not implemented"


class TestGetCallEndpoint:
    """Tests for GET /api/calls/{call_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_call_returns_message(self, client: AsyncClient):
        """Test get call endpoint returns not implemented message."""
        call_id = "test-call-123"
        response = await client.get(f"/api/calls/{call_id}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Get call {call_id} - not implemented"

    @pytest.mark.asyncio
    async def test_get_call_with_uuid(self, client: AsyncClient):
        """Test get call endpoint with UUID format."""
        call_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(f"/api/calls/{call_id}")

        assert response.status_code == 200
        assert call_id in response.json()["message"]


class TestUploadCallEndpoint:
    """Tests for POST /api/calls/upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_call_returns_message(self, client: AsyncClient):
        """Test upload call endpoint returns not implemented message."""
        response = await client.post("/api/calls/upload")

        assert response.status_code == 200
        assert response.json()["message"] == "Upload call - not implemented"


class TestGetCallAnalysisEndpoint:
    """Tests for GET /api/calls/{call_id}/analysis endpoint."""

    @pytest.mark.asyncio
    async def test_get_call_analysis_returns_message(self, client: AsyncClient):
        """Test get call analysis endpoint returns not implemented message."""
        call_id = "test-call-123"
        response = await client.get(f"/api/calls/{call_id}/analysis")

        assert response.status_code == 200
        assert response.json()["message"] == f"Get call analysis {call_id} - not implemented"


class TestReanalyzeCallEndpoint:
    """Tests for POST /api/calls/{call_id}/reanalyze endpoint."""

    @pytest.mark.asyncio
    async def test_reanalyze_call_returns_message(self, client: AsyncClient):
        """Test reanalyze call endpoint returns not implemented message."""
        call_id = "test-call-123"
        response = await client.post(f"/api/calls/{call_id}/reanalyze")

        assert response.status_code == 200
        assert response.json()["message"] == f"Reanalyze call {call_id} - not implemented"
