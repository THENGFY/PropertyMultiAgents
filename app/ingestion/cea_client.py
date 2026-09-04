import asyncio
import logging
from typing import Any
import httpx

from app.config import settings
from app.ingestion.synthetic_data import CEASyntheticGenerator
from app.schemas.raw import RawCEASalespersonPayload, RawCEATransactionPayload
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class CEAClient:
    """Client for ingesting CEA datasets with retry, rate-limiting, and fallback support."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.DATA_GOV_SG_API_URL
        self.max_retries = 3
        self.backoff_factor = 0.5

    async def fetch_dataset_records(
        self, resource_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch records from data.gov.sg with exponential backoff for 429/500 errors."""
        url = self.base_url
        params = {"resource_id": resource_id, "limit": limit, "offset": offset}

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("result", {}).get("records", [])
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            f"[TRANSIENT_HTTP_{resp.status_code}] Error fetching CEA dataset. Retrying ({attempt}/{self.max_retries})..."
                        )
                        await asyncio.sleep(self.backoff_factor * attempt)
                    else:
                        logger.error(
                            f"[HTTP_{resp.status_code}] Non-retryable HTTP error: {resp.text}"
                        )
                        break
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    f"[NETWORK_ERROR] {exc} on attempt {attempt}/{self.max_retries}. Backing off..."
                )
                await asyncio.sleep(self.backoff_factor * attempt)

        return []

    def validate_salesperson_payload(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        """Validate salesperson records using Pydantic RawCEASalespersonPayload."""
        validated = []
        schema_failures = 0
        for r in records:
            try:
                item = RawCEASalespersonPayload.model_validate(r)
                validated.append(r)
            except ValidationError as err:
                schema_failures += 1
                logger.warning(f"[SCHEMA_VALIDATION_ERROR] Malformed salesperson payload: {err}")
        return validated, schema_failures

    def validate_transaction_payload(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        """Validate transaction records using Pydantic RawCEATransactionPayload."""
        validated = []
        schema_failures = 0
        for r in records:
            try:
                item = RawCEATransactionPayload.model_validate(r)
                validated.append(r)
            except ValidationError as err:
                schema_failures += 1
                logger.warning(f"[SCHEMA_VALIDATION_ERROR] Malformed transaction payload: {err}")
        return validated, schema_failures

    async def ingest_raw_feed(
        self, use_fixtures: bool = False, sample_size: int = 150
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch and validate both agent profiles and property transactions."""
        agents: list[dict[str, Any]] = []
        transactions: list[dict[str, Any]] = []

        if not use_fixtures:
            try:
                raw_agents = await self.fetch_dataset_records(
                    settings.CEA_SALESPERSON_RESOURCE_ID, limit=sample_size
                )
                raw_tx = await self.fetch_dataset_records(
                    settings.CEA_TRANSACTION_RESOURCE_ID, limit=sample_size * 5
                )
                if raw_agents and raw_tx:
                    val_agents, fail_a = self.validate_salesperson_payload(raw_agents)
                    val_tx, fail_t = self.validate_transaction_payload(raw_tx)
                    if val_agents and val_tx:
                        agents = val_agents
                        transactions = val_tx
                        logger.info(f"Successfully ingested live data: {len(agents)} agents, {len(transactions)} txs (schema fails: {fail_a+fail_t})")
            except Exception as e:
                logger.warning(f"[INGEST_EXCEPTION] Live fetch failed: {e}. Falling back to synthetic dataset.")

        if not agents or not transactions:
            logger.info("Using high-fidelity synthetic CEA dataset for ingestion.")
            agents = CEASyntheticGenerator.generate_agents(count=sample_size)
            transactions = CEASyntheticGenerator.generate_transactions(agents=agents)

        return agents, transactions
