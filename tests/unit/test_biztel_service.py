"""
Unit tests for Biztel API client service.

Tests use mocks to avoid actual API calls to Biztel.
"""
import os

# Set test environment before imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"

# Patch JSONB to JSON for SQLite compatibility
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect
pg_dialect.JSONB = JSON

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.biztel import (
    BiztelClient,
    BiztelClientFactory,
    BiztelCredentials,
    BiztelAPIError,
    BiztelAuthError,
    BiztelNotFoundError,
    BiztelRateLimitError,
    BiztelEventType,
    BiztelContentType,
    CallHistoryRecord,
    get_biztel_client_for_tenant,
)


@pytest.fixture
def credentials():
    """Create test Biztel credentials."""
    return BiztelCredentials(
        api_key="test-api-key-12345",
        api_secret="test-api-secret",
        base_url="https://test.biztel.jp:8000",
    )


@pytest.fixture
def biztel_client(credentials):
    """Create a BiztelClient instance."""
    return BiztelClient(credentials)


class TestBiztelCredentials:
    """Tests for BiztelCredentials dataclass."""

    def test_credentials_creation(self):
        """Test creating BiztelCredentials."""
        creds = BiztelCredentials(
            api_key="key-123",
            api_secret="secret-456",
            base_url="https://example.biztel.jp:8000",
        )

        assert creds.api_key == "key-123"
        assert creds.api_secret == "secret-456"
        assert creds.base_url == "https://example.biztel.jp:8000"


class TestBiztelEventType:
    """Tests for BiztelEventType enum."""

    def test_event_type_values(self):
        """Test BiztelEventType enum has expected values."""
        assert BiztelEventType.CONNECT.value == "CONNECT"
        assert BiztelEventType.COMPLETECALLER.value == "COMPLETECALLER"
        assert BiztelEventType.COMPLETEAGENT.value == "COMPLETEAGENT"
        assert BiztelEventType.ABANDON.value == "ABANDON"
        assert BiztelEventType.EXITWITHTIMEOUT.value == "EXITWITHTIMEOUT"

    def test_event_type_count(self):
        """Test BiztelEventType has 5 members."""
        assert len(BiztelEventType) == 5


class TestBiztelContentType:
    """Tests for BiztelContentType enum."""

    def test_content_type_values(self):
        """Test BiztelContentType enum has expected values."""
        assert BiztelContentType.MONAURAL.value == "monaural"
        assert BiztelContentType.LEFT.value == "left"
        assert BiztelContentType.RIGHT.value == "right"


class TestBiztelExceptions:
    """Tests for Biztel exception classes."""

    def test_api_error(self):
        """Test BiztelAPIError creation."""
        error = BiztelAPIError("Server error", status_code=500)
        assert str(error) == "Server error"
        assert error.status_code == 500

    def test_auth_error(self):
        """Test BiztelAuthError creation."""
        error = BiztelAuthError("Authentication failed", status_code=401)
        assert isinstance(error, BiztelAPIError)
        assert error.status_code == 401

    def test_rate_limit_error(self):
        """Test BiztelRateLimitError creation."""
        error = BiztelRateLimitError("Rate limit exceeded", status_code=429)
        assert isinstance(error, BiztelAPIError)
        assert error.status_code == 429

    def test_not_found_error(self):
        """Test BiztelNotFoundError creation."""
        error = BiztelNotFoundError("Resource not found", status_code=404)
        assert isinstance(error, BiztelAPIError)
        assert error.status_code == 404

    def test_error_without_status_code(self):
        """Test BiztelAPIError without status code."""
        error = BiztelAPIError("Generic error")
        assert error.status_code is None


class TestBiztelClientInit:
    """Tests for BiztelClient initialization."""

    def test_client_creation(self, credentials):
        """Test creating BiztelClient."""
        client = BiztelClient(credentials)

        assert client.credentials == credentials
        assert client._last_request_time == 0

    def test_get_headers(self, biztel_client):
        """Test _get_headers returns proper authorization header."""
        headers = biztel_client._get_headers()

        assert headers["Authorization"] == "Token test-api-key-12345"
        assert headers["Content-Type"] == "application/json"


class TestBiztelClientDateParsing:
    """Tests for _parse_datetime method."""

    def test_parse_iso_format(self, biztel_client):
        """Test parsing ISO format datetime."""
        result = biztel_client._parse_datetime("2024-01-15T10:30:00")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_space_separated_format(self, biztel_client):
        """Test parsing space-separated datetime."""
        result = biztel_client._parse_datetime("2024-01-15 10:30:00")

        assert result is not None
        assert result.year == 2024

    def test_parse_none(self, biztel_client):
        """Test parsing None returns None."""
        result = biztel_client._parse_datetime(None)
        assert result is None

    def test_parse_empty_string(self, biztel_client):
        """Test parsing empty string returns None."""
        result = biztel_client._parse_datetime("")
        assert result is None

    def test_parse_invalid_format(self, biztel_client):
        """Test parsing invalid format returns None."""
        result = biztel_client._parse_datetime("not-a-date")
        assert result is None


class TestBiztelClientRequest:
    """Tests for _request method."""

    @pytest.mark.asyncio
    async def test_request_success(self, biztel_client):
        """Test successful API request."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.biztel.httpx.AsyncClient") as MockClient:
            mock_http_client = AsyncMock()
            mock_http_client.request = AsyncMock(return_value=mock_response)
            mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http_client

            with patch.object(biztel_client, "_rate_limit_wait", new_callable=AsyncMock):
                response = await biztel_client._request("GET", "/public/api/v1/queue_log")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_auth_error(self, biztel_client):
        """Test request raises BiztelAuthError on 401."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        with patch("app.services.biztel.httpx.AsyncClient") as MockClient:
            mock_http_client = AsyncMock()
            mock_http_client.request = AsyncMock(return_value=mock_response)
            mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http_client

            with patch.object(biztel_client, "_rate_limit_wait", new_callable=AsyncMock):
                with pytest.raises(BiztelAuthError):
                    await biztel_client._request("GET", "/public/api/v1/queue_log")

    @pytest.mark.asyncio
    async def test_request_not_found_error(self, biztel_client):
        """Test request raises BiztelNotFoundError on 404."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404

        with patch("app.services.biztel.httpx.AsyncClient") as MockClient:
            mock_http_client = AsyncMock()
            mock_http_client.request = AsyncMock(return_value=mock_response)
            mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http_client

            with patch.object(biztel_client, "_rate_limit_wait", new_callable=AsyncMock):
                with pytest.raises(BiztelNotFoundError):
                    await biztel_client._request("GET", "/public/api/v1/monitor/invalid")

    @pytest.mark.asyncio
    async def test_request_server_error(self, biztel_client):
        """Test request raises BiztelAPIError on 500."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500

        with patch("app.services.biztel.httpx.AsyncClient") as MockClient:
            mock_http_client = AsyncMock()
            mock_http_client.request = AsyncMock(return_value=mock_response)
            mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http_client

            with patch.object(biztel_client, "_rate_limit_wait", new_callable=AsyncMock):
                with pytest.raises(BiztelAPIError):
                    await biztel_client._request("GET", "/test")


class TestGetCallHistory:
    """Tests for get_call_history method."""

    @pytest.mark.asyncio
    async def test_get_call_history_success(self, biztel_client):
        """Test successful call history retrieval."""
        api_response = {
            "results": [
                {
                    "request_id": "REQ-001",
                    "start_time": "2024-01-15 10:30:00",
                    "caller_id": "03-1234-5678",
                    "called_id": "0120-123-456",
                    "hold_time": 15,
                    "call_time": 300,
                    "account_id": 101,
                    "account_name": "Operator A",
                    "queue_id": 1,
                    "queue_name": "Support",
                    "queue_exten": "1001",
                    "business_name": "Sales",
                    "event": "COMPLETEAGENT",
                    "monitor_logs": 1,
                },
                {
                    "request_id": "REQ-002",
                    "start_time": "2024-01-15 11:00:00",
                    "caller_id": "06-9876-5432",
                    "called_id": "0120-123-456",
                    "hold_time": 5,
                    "call_time": 120,
                    "account_id": 102,
                    "account_name": "Operator B",
                    "queue_id": 1,
                    "queue_name": "Support",
                    "queue_exten": "1002",
                    "business_name": "Support",
                    "event": "COMPLETECALLER",
                    "monitor_logs": 0,
                },
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = api_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response):
            records = await biztel_client.get_call_history(
                start_date=datetime(2024, 1, 15, 0, 0, 0),
                end_date=datetime(2024, 1, 15, 23, 59, 59),
            )

        assert len(records) == 2
        assert isinstance(records[0], CallHistoryRecord)
        assert records[0].request_id == "REQ-001"
        assert records[0].caller_id == "03-1234-5678"
        assert records[0].account_id == "101"
        assert records[0].account_name == "Operator A"
        assert records[0].has_recording is True
        assert records[1].has_recording is False

    @pytest.mark.asyncio
    async def test_get_call_history_empty(self, biztel_client):
        """Test call history retrieval with no results."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response):
            records = await biztel_client.get_call_history(
                start_date=datetime(2024, 1, 15, 0, 0, 0),
                end_date=datetime(2024, 1, 15, 23, 59, 59),
            )

        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_get_call_history_with_filters(self, biztel_client):
        """Test call history retrieval with filters."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await biztel_client.get_call_history(
                start_date=datetime(2024, 1, 15, 0, 0, 0),
                end_date=datetime(2024, 1, 15, 23, 59, 59),
                queue_id=5,
                account_id=101,
                events=[BiztelEventType.CONNECT],
                limit=100,
            )

            call_args = mock_req.call_args
            params = call_args[1]["params"]
            assert params["queue_id"] == 5
            assert params["account_id"] == 101
            assert params["event"] == "CONNECT"
            assert params["limit"] == 100

    @pytest.mark.asyncio
    async def test_get_call_history_default_events(self, biztel_client):
        """Test call history defaults to completed calls."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await biztel_client.get_call_history(
                start_date=datetime(2024, 1, 15),
                end_date=datetime(2024, 1, 16),
            )

            params = mock_req.call_args[1]["params"]
            assert "COMPLETECALLER" in params["event"]
            assert "COMPLETEAGENT" in params["event"]

    @pytest.mark.asyncio
    async def test_get_call_history_limit_capped_at_10000(self, biztel_client):
        """Test call history limit is capped at 10000."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await biztel_client.get_call_history(
                start_date=datetime(2024, 1, 15),
                end_date=datetime(2024, 1, 16),
                limit=50000,
            )

            params = mock_req.call_args[1]["params"]
            assert params["limit"] == 10000


class TestDownloadRecording:
    """Tests for download_recording method."""

    @pytest.mark.asyncio
    async def test_download_recording_success(self, biztel_client):
        """Test successful recording download."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"fake-audio-content-mp3"
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response):
            audio_data = await biztel_client.download_recording("REQ-001")

        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0

    @pytest.mark.asyncio
    async def test_download_recording_with_content_type(self, biztel_client):
        """Test recording download with specific content type."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"stereo-audio"
        mock_response.raise_for_status = MagicMock()

        with patch.object(biztel_client, "_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
            await biztel_client.download_recording("REQ-001", BiztelContentType.LEFT)

            call_args = mock_req.call_args
            assert call_args[1]["params"]["content_type"] == "left"

    @pytest.mark.asyncio
    async def test_download_recording_not_found(self, biztel_client):
        """Test recording download for non-existent recording."""
        with patch.object(biztel_client, "_request", new_callable=AsyncMock, side_effect=BiztelNotFoundError("Not found", 404)):
            with pytest.raises(BiztelNotFoundError):
                await biztel_client.download_recording("NONEXISTENT-REQ")


class TestTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_connection_success(self, biztel_client):
        """Test successful connection test."""
        with patch.object(biztel_client, "get_call_history", new_callable=AsyncMock, return_value=[]):
            result = await biztel_client.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_connection_auth_failure(self, biztel_client):
        """Test connection test with auth failure."""
        with patch.object(
            biztel_client,
            "get_call_history",
            new_callable=AsyncMock,
            side_effect=BiztelAuthError("Auth failed", 401),
        ):
            result = await biztel_client.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_connection_generic_failure(self, biztel_client):
        """Test connection test with generic failure."""
        with patch.object(
            biztel_client,
            "get_call_history",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ):
            result = await biztel_client.test_connection()

        assert result is False


class TestBiztelClientFactory:
    """Tests for BiztelClientFactory."""

    def setup_method(self):
        """Clear cached clients before each test."""
        BiztelClientFactory._clients.clear()

    def test_get_client_creates_new(self):
        """Test get_client creates new client for new tenant."""
        tenant_id = uuid.uuid4()
        credentials = BiztelCredentials("key", "secret", "https://test.biztel.jp:8000")

        client = BiztelClientFactory.get_client(tenant_id, credentials)

        assert isinstance(client, BiztelClient)
        assert client.credentials == credentials

    def test_get_client_returns_cached(self):
        """Test get_client returns cached client for same tenant."""
        tenant_id = uuid.uuid4()
        credentials = BiztelCredentials("key", "secret", "https://test.biztel.jp:8000")

        client1 = BiztelClientFactory.get_client(tenant_id, credentials)
        client2 = BiztelClientFactory.get_client(tenant_id, credentials)

        assert client1 is client2

    def test_get_client_different_tenants(self):
        """Test get_client creates different clients for different tenants."""
        tenant1 = uuid.uuid4()
        tenant2 = uuid.uuid4()
        creds1 = BiztelCredentials("key1", "secret1", "https://test1.biztel.jp:8000")
        creds2 = BiztelCredentials("key2", "secret2", "https://test2.biztel.jp:8000")

        client1 = BiztelClientFactory.get_client(tenant1, creds1)
        client2 = BiztelClientFactory.get_client(tenant2, creds2)

        assert client1 is not client2

    def test_clear_client(self):
        """Test clear_client removes cached client."""
        tenant_id = uuid.uuid4()
        credentials = BiztelCredentials("key", "secret", "https://test.biztel.jp:8000")

        client1 = BiztelClientFactory.get_client(tenant_id, credentials)
        BiztelClientFactory.clear_client(tenant_id)
        client2 = BiztelClientFactory.get_client(tenant_id, credentials)

        assert client1 is not client2

    def test_clear_nonexistent_client(self):
        """Test clear_client for non-existent tenant doesn't raise."""
        BiztelClientFactory.clear_client(uuid.uuid4())


class TestGetBiztelClientForTenant:
    """Tests for get_biztel_client_for_tenant helper."""

    def setup_method(self):
        BiztelClientFactory._clients.clear()

    @pytest.mark.asyncio
    async def test_get_client_for_tenant(self):
        """Test creating client for tenant."""
        tenant_id = uuid.uuid4()
        client = await get_biztel_client_for_tenant(
            tenant_id=tenant_id,
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://test.biztel.jp:8000",
        )

        assert isinstance(client, BiztelClient)
        assert client.credentials.api_key == "test-key"
        assert client.credentials.base_url == "https://test.biztel.jp:8000"
