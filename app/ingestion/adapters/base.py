import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BaseDatasetAdapter(ABC):
    """Abstract base adapter for ingesting external Singapore public datasets with retry and rate-limiting."""

    def __init__(
        self,
        base_url: str | None = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float = 5.0,
    ):
        self.base_url = base_url or settings.DATA_GOV_SG_API_URL
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

    async def fetch_datastore_records(
        self, resource_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch datastore records from data.gov.sg with exponential backoff on 429/5xx errors."""
        params = {"resource_id": resource_id, "limit": limit, "offset": offset}

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(self.base_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("result", {}).get("records", [])
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            f"[TRANSIENT_HTTP_{resp.status_code}] Adapter fetch error. Retrying ({attempt}/{self.max_retries})..."
                        )
                        await asyncio.sleep(self.backoff_factor * attempt)
                    else:
                        logger.error(
                            f"[HTTP_{resp.status_code}] Non-retryable adapter HTTP error: {resp.text}"
                        )
                        break
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    f"[ADAPTER_NETWORK_ERROR] {exc} on attempt {attempt}/{self.max_retries}. Backing off..."
                )
                await asyncio.sleep(self.backoff_factor * attempt)

        return []

    @abstractmethod
    async def fetch_data(self, sample_size: int = 100) -> list[dict[str, Any]]:
        """Fetch and return raw records for the specialized dataset."""
        pass
