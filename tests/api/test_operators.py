"""
API tests for operator endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListOperatorsEndpoint:
    """Tests for GET /api/operators endpoint."""

    @pytest.mark.asyncio
    async def test_list_operators_returns_message(self, client: AsyncClient):
        """Test list operators endpoint returns not implemented message."""
        response = await client.get("/api/operators")

        assert response.status_code == 200
        assert response.json()["message"] == "List operators - not implemented"

    @pytest.mark.asyncio
    async def test_list_operators_method_not_allowed(self, client: AsyncClient):
        """Test that POST method is not allowed on list endpoint."""
        response = await client.post("/api/operators")

        assert response.status_code == 405


class TestGetOperatorEndpoint:
    """Tests for GET /api/operators/{operator_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_operator_returns_message(self, client: AsyncClient):
        """Test get operator endpoint returns not implemented message."""
        operator_id = "test-op-123"
        response = await client.get(f"/api/operators/{operator_id}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Get operator {operator_id} - not implemented"

    @pytest.mark.asyncio
    async def test_get_operator_with_uuid(self, client: AsyncClient):
        """Test get operator endpoint with UUID format."""
        operator_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(f"/api/operators/{operator_id}")

        assert response.status_code == 200
        assert operator_id in response.json()["message"]

    @pytest.mark.asyncio
    async def test_get_operator_with_special_chars(self, client: AsyncClient):
        """Test get operator endpoint with special characters in ID."""
        operator_id = "BIZ-OP-001"
        response = await client.get(f"/api/operators/{operator_id}")

        assert response.status_code == 200
        assert operator_id in response.json()["message"]


class TestGetOperatorStatsEndpoint:
    """Tests for GET /api/operators/{operator_id}/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_operator_stats_returns_message(self, client: AsyncClient):
        """Test get operator stats endpoint returns not implemented message."""
        operator_id = "test-op-123"
        response = await client.get(f"/api/operators/{operator_id}/stats")

        assert response.status_code == 200
        assert response.json()["message"] == f"Get operator stats {operator_id} - not implemented"

    @pytest.mark.asyncio
    async def test_get_operator_stats_with_uuid(self, client: AsyncClient):
        """Test get operator stats endpoint with UUID format."""
        operator_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(f"/api/operators/{operator_id}/stats")

        assert response.status_code == 200
        assert operator_id in response.json()["message"]

    @pytest.mark.asyncio
    async def test_stats_and_detail_different_endpoints(self, client: AsyncClient):
        """Test that stats and detail are different endpoints."""
        operator_id = "test-op-123"

        detail_response = await client.get(f"/api/operators/{operator_id}")
        stats_response = await client.get(f"/api/operators/{operator_id}/stats")

        assert detail_response.status_code == 200
        assert stats_response.status_code == 200
        assert detail_response.json() != stats_response.json()
        assert "stats" in stats_response.json()["message"]
        assert "stats" not in detail_response.json()["message"]
