"""
API tests for settings endpoints.

Tests the fully implemented settings endpoints for operation flows,
analysis prompts, and Biztel API configuration with RBAC.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation_flow import OperationFlow
from app.models.analysis_prompt import AnalysisPrompt, PromptType
from app.models.tenant import Tenant
from app.models.user import User


# ============================================================
# Operation Flows
# ============================================================


class TestListFlowsEndpoint:
    """Tests for GET /api/settings/flows endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.get("/api/settings/flows")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot access flows (requires QAUser)."""
        response = await client.get(
            "/api/settings/flows", headers=operator_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_flows_empty(self, client: AsyncClient, auth_headers: dict):
        """Test list flows returns empty when none exist."""
        response = await client.get("/api/settings/flows", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_flows_with_flow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_operation_flow: OperationFlow,
    ):
        """Test list flows returns existing flows."""
        response = await client.get("/api/settings/flows", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_operation_flow.id)
        assert data["items"][0]["name"] == "Standard Inquiry Flow"
        assert data["items"][0]["is_active"] is True


class TestCreateFlowEndpoint:
    """Tests for POST /api/settings/flows endpoint."""

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot create flows."""
        response = await client.post(
            "/api/settings/flows",
            headers=operator_auth_headers,
            params={"name": "Test Flow"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_flow_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a new operation flow."""
        response = await client.post(
            "/api/settings/flows",
            headers=auth_headers,
            params={
                "name": "New Test Flow",
                "classification_criteria": "Test criteria for classification",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Test Flow"
        assert data["classification_criteria"] == "Test criteria for classification"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_flow_name_required(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that name is required when creating a flow."""
        response = await client.post(
            "/api/settings/flows",
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetFlowEndpoint:
    """Tests for GET /api/settings/flows/{flow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_flow_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_operation_flow: OperationFlow,
    ):
        """Test getting a specific flow by ID."""
        response = await client.get(
            f"/api/settings/flows/{test_operation_flow.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_operation_flow.id)
        assert data["name"] == "Standard Inquiry Flow"
        assert data["flow_definition"] is not None
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_flow_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting a non-existent flow returns 404."""
        flow_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/settings/flows/{flow_id}", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Operation flow not found"


class TestUpdateFlowEndpoint:
    """Tests for PUT /api/settings/flows/{flow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_flow_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_operation_flow: OperationFlow,
    ):
        """Test updating a flow's name."""
        response = await client.put(
            f"/api/settings/flows/{test_operation_flow.id}",
            headers=auth_headers,
            params={"name": "Updated Flow Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Flow Name"

    @pytest.mark.asyncio
    async def test_update_flow_deactivate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_operation_flow: OperationFlow,
    ):
        """Test deactivating a flow."""
        response = await client.put(
            f"/api/settings/flows/{test_operation_flow.id}",
            headers=auth_headers,
            params={"is_active": "false"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_flow_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating a non-existent flow returns 404."""
        flow_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/settings/flows/{flow_id}",
            headers=auth_headers,
            params={"name": "New Name"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Operation flow not found"


class TestDeleteFlowEndpoint:
    """Tests for DELETE /api/settings/flows/{flow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_flow_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_operation_flow: OperationFlow,
    ):
        """Test deleting a flow."""
        response = await client.delete(
            f"/api/settings/flows/{test_operation_flow.id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Operation flow deleted"

        # Verify it's actually deleted
        response = await client.get(
            f"/api/settings/flows/{test_operation_flow.id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_flow_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting a non-existent flow returns 404."""
        flow_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/settings/flows/{flow_id}", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Operation flow not found"


# ============================================================
# Analysis Prompts
# ============================================================


class TestListPromptsEndpoint:
    """Tests for GET /api/settings/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.get("/api/settings/prompts")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot access prompts."""
        response = await client.get(
            "/api/settings/prompts", headers=operator_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_prompts_empty(self, client: AsyncClient, auth_headers: dict):
        """Test list prompts returns empty when none exist."""
        response = await client.get("/api/settings/prompts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_prompts_with_prompt(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test list prompts returns existing prompts."""
        response = await client.get("/api/settings/prompts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_analysis_prompt.id)
        assert data["items"][0]["name"] == "Quality Score Prompt"

    @pytest.mark.asyncio
    async def test_list_prompts_filter_by_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test filtering prompts by type."""
        response = await client.get(
            "/api/settings/prompts",
            headers=auth_headers,
            params={"prompt_type": "quality_score"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        # Filter with non-matching type
        response = await client.get(
            "/api/settings/prompts",
            headers=auth_headers,
            params={"prompt_type": "summary"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0


class TestCreatePromptEndpoint:
    """Tests for POST /api/settings/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_create_prompt_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a new analysis prompt."""
        response = await client.post(
            "/api/settings/prompts",
            headers=auth_headers,
            params={
                "prompt_type": "quality_score",
                "name": "New Quality Prompt",
                "prompt_text": "Evaluate the quality of this call.",
                "description": "A test prompt",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Quality Prompt"
        assert data["prompt_text"] == "Evaluate the quality of this call."
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_prompt_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that required fields are validated."""
        response = await client.post(
            "/api/settings/prompts",
            headers=auth_headers,
            params={"name": "Incomplete Prompt"},
        )
        assert response.status_code == 422


class TestGetPromptEndpoint:
    """Tests for GET /api/settings/prompts/{prompt_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_prompt_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test getting a specific prompt."""
        response = await client.get(
            f"/api/settings/prompts/{test_analysis_prompt.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_analysis_prompt.id)
        assert data["name"] == "Quality Score Prompt"
        assert data["prompt_text"] == "Please evaluate the following call transcript for quality."
        assert data["is_default"] is False

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting a non-existent prompt returns 404."""
        prompt_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/settings/prompts/{prompt_id}", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"


class TestUpdatePromptEndpoint:
    """Tests for PUT /api/settings/prompts/{prompt_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_prompt_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test updating a prompt's name."""
        response = await client.put(
            f"/api/settings/prompts/{test_analysis_prompt.id}",
            headers=auth_headers,
            params={"name": "Updated Prompt Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Prompt Name"

    @pytest.mark.asyncio
    async def test_update_prompt_text(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test updating a prompt's text."""
        new_text = "Updated prompt text for evaluation."
        response = await client.put(
            f"/api/settings/prompts/{test_analysis_prompt.id}",
            headers=auth_headers,
            params={"prompt_text": new_text},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_text"] == new_text

    @pytest.mark.asyncio
    async def test_update_prompt_deactivate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test deactivating a prompt."""
        response = await client.put(
            f"/api/settings/prompts/{test_analysis_prompt.id}",
            headers=auth_headers,
            params={"is_active": "false"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating a non-existent prompt returns 404."""
        prompt_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/settings/prompts/{prompt_id}",
            headers=auth_headers,
            params={"name": "New Name"},
        )

        assert response.status_code == 404


class TestDeletePromptEndpoint:
    """Tests for DELETE /api/settings/prompts/{prompt_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_prompt_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_analysis_prompt: AnalysisPrompt,
    ):
        """Test deleting a non-default prompt."""
        response = await client.delete(
            f"/api/settings/prompts/{test_analysis_prompt.id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Prompt deleted"

        # Verify it's actually deleted
        response = await client.get(
            f"/api/settings/prompts/{test_analysis_prompt.id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_default_prompt_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_default_prompt: AnalysisPrompt,
    ):
        """Test that default prompts cannot be deleted."""
        response = await client.delete(
            f"/api/settings/prompts/{test_default_prompt.id}", headers=auth_headers
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot delete default prompt"

    @pytest.mark.asyncio
    async def test_delete_prompt_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting a non-existent prompt returns 404."""
        prompt_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/settings/prompts/{prompt_id}", headers=auth_headers
        )

        assert response.status_code == 404


# ============================================================
# Biztel Settings
# ============================================================


class TestGetBiztelSettingsEndpoint:
    """Tests for GET /api/settings/biztel endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.get("/api/settings/biztel")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot access Biztel settings (requires AdminUser)."""
        response = await client.get(
            "/api/settings/biztel", headers=operator_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_biztel_settings_unconfigured(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting Biztel settings when not configured."""
        response = await client.get("/api/settings/biztel", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["base_url"] == ""
        assert data["api_key_masked"] == ""


class TestUpdateBiztelSettingsEndpoint:
    """Tests for PUT /api/settings/biztel endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.put("/api/settings/biztel")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot update Biztel settings."""
        response = await client.put(
            "/api/settings/biztel",
            headers=operator_auth_headers,
            json={
                "api_key": "test-key",
                "base_url": "https://test.biztel.jp:8000",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_biztel_settings_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating Biztel settings."""
        response = await client.put(
            "/api/settings/biztel",
            headers=auth_headers,
            json={
                "api_key": "test-api-key-12345678",
                "base_url": "https://test.biztel.jp:8000",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert data["base_url"] == "https://test.biztel.jp:8000"
        # API key should be masked
        assert data["api_key_masked"].endswith("5678")
        assert "****" in data["api_key_masked"]

    @pytest.mark.asyncio
    async def test_update_biztel_settings_validation(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that required fields are validated."""
        response = await client.put(
            "/api/settings/biztel",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 422


class TestTestBiztelConnectionEndpoint:
    """Tests for POST /api/settings/biztel/test endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.post("/api/settings/biztel/test")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_forbidden(
        self, client: AsyncClient, operator_auth_headers: dict
    ):
        """Test that OPERATOR role cannot test Biztel connection."""
        response = await client.post(
            "/api/settings/biztel/test", headers=operator_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_test_connection_not_configured(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test connection test when credentials are not configured."""
        response = await client.post(
            "/api/settings/biztel/test", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not configured" in data["message"]


class TestBiztelSyncEndpoint:
    """Tests for POST /api/settings/biztel/sync endpoint."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_403(self, client: AsyncClient):
        """Test that unauthenticated request returns 403."""
        response = await client.post("/api/settings/biztel/sync")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_sync_not_configured(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test sync when Biztel credentials are not configured."""
        response = await client.post(
            "/api/settings/biztel/sync",
            headers=auth_headers,
            json={
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-31T23:59:59",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Biztel API credentials not configured"
