import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


class BiztelEventType(str, Enum):
    """Biztel call event types."""
    CONNECT = "CONNECT"  # 応答
    COMPLETECALLER = "COMPLETECALLER"  # 切断（お客様）
    COMPLETEAGENT = "COMPLETEAGENT"  # 切断（エージェント）
    ABANDON = "ABANDON"  # 放棄呼
    EXITWITHTIMEOUT = "EXITWITHTIMEOUT"  # 応答不能時ルール


class BiztelContentType(str, Enum):
    """Audio content types for recording download."""
    MONAURAL = "monaural"  # 通常（ミックス）
    LEFT = "left"  # 相手側
    RIGHT = "right"  # オペレータ側


class BiztelAPIError(Exception):
    """Base exception for Biztel API errors."""
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BiztelAuthError(BiztelAPIError):
    """Authentication error."""
    pass


class BiztelRateLimitError(BiztelAPIError):
    """Rate limit exceeded."""
    pass


class BiztelNotFoundError(BiztelAPIError):
    """Resource not found."""
    pass


@dataclass
class BiztelCredentials:
    """Biztel API credentials for a tenant."""
    api_key: str
    api_secret: str
    base_url: str


@dataclass
class CallHistoryRecord:
    """Parsed call history record from Biztel API."""
    request_id: str
    start_time: datetime
    caller_id: str | None
    called_id: str | None
    hold_time: int | None  # seconds
    call_time: int | None  # seconds
    account_id: str | None  # operator ID
    account_name: str | None  # operator name
    queue_id: int | None  # call center ID
    queue_name: str | None  # call center name
    queue_exten: str | None  # call center extension
    business_name: str | None  # business label
    event: str | None
    has_recording: bool


class BiztelClient:
    """
    Async client for Biztel API.

    Handles authentication, rate limiting, and retries.
    """

    def __init__(self, credentials: BiztelCredentials):
        self.credentials = credentials
        self._last_request_time: float = 0
        self._rate_limit_delay = settings.BIZTEL_API_RATE_LIMIT_DELAY

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Token {self.credentials.api_key}",
            "Content-Type": "application/json",
        }

    async def _rate_limit_wait(self) -> None:
        """Wait to respect rate limit (10 requests/second)."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse Biztel datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace(" ", "T"))
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, BiztelRateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make a rate-limited request with retry logic."""
        await self._rate_limit_wait()

        url = f"{self.credentials.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=settings.BIZTEL_API_TIMEOUT) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                **kwargs,
            )

        if response.status_code == 401:
            raise BiztelAuthError("Authentication failed", status_code=401)
        if response.status_code == 404:
            raise BiztelNotFoundError("Resource not found", status_code=404)
        if response.status_code == 429:
            raise BiztelRateLimitError("Rate limit exceeded", status_code=429)
        if response.status_code >= 500:
            raise BiztelAPIError(f"Server error: {response.status_code}", status_code=response.status_code)

        response.raise_for_status()
        return response

    async def get_call_history(
        self,
        start_date: datetime,
        end_date: datetime,
        queue_id: int | None = None,
        account_id: int | None = None,
        events: list[BiztelEventType] | None = None,
        limit: int = 10000,
    ) -> list[CallHistoryRecord]:
        """
        Get call history from Biztel API.

        Args:
            start_date: Start of date range
            end_date: End of date range
            queue_id: Filter by call center ID
            account_id: Filter by operator ID
            events: Filter by event types (defaults to completed calls)
            limit: Maximum records to return (max 10000 per request)

        Returns:
            List of CallHistoryRecord objects
        """
        params: dict[str, Any] = {
            "created_at_start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at_end": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "limit": min(limit, 10000),
        }

        if queue_id:
            params["queue_id"] = queue_id
        if account_id:
            params["account_id"] = account_id
        if events:
            params["event"] = ",".join(e.value for e in events)
        else:
            # Default to completed calls only
            params["event"] = f"{BiztelEventType.COMPLETECALLER.value},{BiztelEventType.COMPLETEAGENT.value}"

        response = await self._request("GET", "/public/api/v1/queue_log", params=params)
        data = response.json()

        records = []
        for item in data.get("results", data if isinstance(data, list) else []):
            record = CallHistoryRecord(
                request_id=item.get("request_id", ""),
                start_time=self._parse_datetime(item.get("start_time")) or datetime.utcnow(),
                caller_id=item.get("caller_id"),
                called_id=item.get("called_id"),
                hold_time=item.get("hold_time"),
                call_time=item.get("call_time"),
                account_id=str(item.get("account_id")) if item.get("account_id") else None,
                account_name=item.get("account_name"),
                queue_id=item.get("queue_id"),
                queue_name=item.get("queue_name"),
                queue_exten=item.get("queue_exten"),
                business_name=item.get("business_name"),
                event=item.get("event"),
                has_recording=item.get("monitor_logs", 0) == 1,
            )
            records.append(record)

        return records

    async def get_call_history_paginated(
        self,
        start_date: datetime,
        end_date: datetime,
        queue_id: int | None = None,
        events: list[BiztelEventType] | None = None,
    ) -> list[CallHistoryRecord]:
        """
        Get all call history with pagination support.

        Handles the 10,000 record limit per request by paginating.
        """
        all_records: list[CallHistoryRecord] = []
        page_size = 10000
        current_start = start_date

        while current_start < end_date:
            # Get records for current time window
            records = await self.get_call_history(
                start_date=current_start,
                end_date=end_date,
                queue_id=queue_id,
                events=events,
                limit=page_size,
            )

            if not records:
                break

            all_records.extend(records)

            # If we got less than page_size, we have all records
            if len(records) < page_size:
                break

            # Move start time to last record's time + 1 second for next page
            last_time = max(r.start_time for r in records)
            current_start = last_time + timedelta(seconds=1)

        return all_records

    async def download_recording(
        self,
        request_id: str,
        content_type: BiztelContentType = BiztelContentType.MONAURAL,
    ) -> bytes:
        """
        Download call recording from Biztel API.

        Args:
            request_id: The request ID of the call
            content_type: Type of recording (monaural, left, right)

        Returns:
            Audio file content as bytes

        Note:
            Recordings are only available for 7 days after the call.
        """
        params = {"content_type": content_type.value}

        response = await self._request(
            "GET",
            f"/public/api/v1/monitor/{request_id}",
            params=params,
        )

        return response.content

    async def test_connection(self) -> bool:
        """Test API connection by making a simple request."""
        try:
            # Try to get a small amount of recent history
            yesterday = datetime.utcnow() - timedelta(days=1)
            today = datetime.utcnow()
            await self.get_call_history(yesterday, today, limit=1)
            return True
        except BiztelAuthError:
            return False
        except Exception:
            return False


class BiztelClientFactory:
    """Factory for creating BiztelClient instances per tenant."""

    _clients: dict[uuid.UUID, BiztelClient] = {}

    @classmethod
    def get_client(cls, tenant_id: uuid.UUID, credentials: BiztelCredentials) -> BiztelClient:
        """Get or create a BiztelClient for a tenant."""
        if tenant_id not in cls._clients:
            cls._clients[tenant_id] = BiztelClient(credentials)
        return cls._clients[tenant_id]

    @classmethod
    def clear_client(cls, tenant_id: uuid.UUID) -> None:
        """Clear cached client for a tenant (e.g., when credentials change)."""
        cls._clients.pop(tenant_id, None)


async def get_biztel_client_for_tenant(
    tenant_id: uuid.UUID,
    api_key: str,
    api_secret: str,
    base_url: str,
) -> BiztelClient:
    """
    Helper to get a BiztelClient for a tenant.

    In production, credentials would be fetched from the database and decrypted.
    """
    credentials = BiztelCredentials(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
    )
    return BiztelClientFactory.get_client(tenant_id, credentials)
