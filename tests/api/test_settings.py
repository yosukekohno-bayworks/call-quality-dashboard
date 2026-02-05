"""
API tests for settings endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListFlowsEndpoint:
    """Tests for GET /api/settings/flows endpoint."""

    @pytest.mark.asyncio
    async def test_list_flows_returns_message(self, client: AsyncClient):
        """Test list flows endpoint returns not implemented message."""
        response = await client.get("/api/settings/flows")

        assert response.status_code == 200
        assert response.json()["message"] == "List flows - not implemented"


class TestCreateFlowEndpoint:
    """Tests for POST /api/settings/flows endpoint."""

    @pytest.mark.asyncio
    async def test_create_flow_returns_message(self, client: AsyncClient):
        """Test create flow endpoint returns not implemented message."""
        response = await client.post("/api/settings/flows")

        assert response.status_code == 200
        assert response.json()["message"] == "Create flow - not implemented"


class TestUpdateFlowEndpoint:
    """Tests for PUT /api/settings/flows/{flow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_flow_returns_message(self, client: AsyncClient):
        """Test update flow endpoint returns not implemented message."""
        flow_id = "test-flow-123"
        response = await client.put(f"/api/settings/flows/{flow_id}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Update flow {flow_id} - not implemented"


class TestDeleteFlowEndpoint:
    """Tests for DELETE /api/settings/flows/{flow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_flow_returns_message(self, client: AsyncClient):
        """Test delete flow endpoint returns not implemented message."""
        flow_id = "test-flow-123"
        response = await client.delete(f"/api/settings/flows/{flow_id}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Delete flow {flow_id} - not implemented"


class TestListPromptsEndpoint:
    """Tests for GET /api/settings/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_list_prompts_returns_message(self, client: AsyncClient):
        """Test list prompts endpoint returns not implemented message."""
        response = await client.get("/api/settings/prompts")

        assert response.status_code == 200
        assert response.json()["message"] == "List prompts - not implemented"


class TestUpdatePromptEndpoint:
    """Tests for PUT /api/settings/prompts/{prompt_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_prompt_returns_message(self, client: AsyncClient):
        """Test update prompt endpoint returns not implemented message."""
        prompt_id = "test-prompt-123"
        response = await client.put(f"/api/settings/prompts/{prompt_id}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Update prompt {prompt_id} - not implemented"


class TestGetBiztelSettingsEndpoint:
    """Tests for GET /api/settings/biztel endpoint."""

    @pytest.mark.asyncio
    async def test_get_biztel_settings_returns_message(self, client: AsyncClient):
        """Test get Biztel settings endpoint returns not implemented message."""
        response = await client.get("/api/settings/biztel")

        assert response.status_code == 200
        assert response.json()["message"] == "Get Biztel settings - not implemented"


class TestUpdateBiztelSettingsEndpoint:
    """Tests for PUT /api/settings/biztel endpoint."""

    @pytest.mark.asyncio
    async def test_update_biztel_settings_returns_message(self, client: AsyncClient):
        """Test update Biztel settings endpoint returns not implemented message."""
        response = await client.put("/api/settings/biztel")

        assert response.status_code == 200
        assert response.json()["message"] == "Update Biztel settings - not implemented"


class TestTestBiztelConnectionEndpoint:
    """Tests for POST /api/settings/biztel/test endpoint."""

    @pytest.mark.asyncio
    async def test_test_biztel_connection_returns_message(self, client: AsyncClient):
        """Test Biztel connection test endpoint returns not implemented message."""
        response = await client.post("/api/settings/biztel/test")

        assert response.status_code == 200
        assert response.json()["message"] == "Test Biztel connection - not implemented"
