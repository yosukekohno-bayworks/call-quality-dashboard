"""
API tests for dashboard analytics endpoints.
"""
import pytest
from httpx import AsyncClient


class TestDashboardSummaryEndpoint:
    """Tests for GET /api/dashboard/summary endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_summary_returns_message(self, client: AsyncClient):
        """Test dashboard summary endpoint returns not implemented message."""
        response = await client.get("/api/dashboard/summary")

        assert response.status_code == 200
        assert response.json()["message"] == "Dashboard summary - not implemented"


class TestDashboardTrendsEndpoint:
    """Tests for GET /api/dashboard/trends endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_trends_returns_message(self, client: AsyncClient):
        """Test dashboard trends endpoint returns not implemented message."""
        response = await client.get("/api/dashboard/trends")

        assert response.status_code == 200
        assert response.json()["message"] == "Dashboard trends - not implemented"


class TestDashboardRankingsEndpoint:
    """Tests for GET /api/dashboard/rankings endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_rankings_returns_message(self, client: AsyncClient):
        """Test dashboard rankings endpoint returns not implemented message."""
        response = await client.get("/api/dashboard/rankings")

        assert response.status_code == 200
        assert response.json()["message"] == "Dashboard rankings - not implemented"
