import logging
from typing import Any
from app.ingestion.adapters.base import BaseDatasetAdapter
from app.ingestion.synthetic_data import CEASyntheticGenerator

logger = logging.getLogger(__name__)


class HDBResaleAdapter(BaseDatasetAdapter):
    """Adapter for ingesting HDB Resale Flat transactions & extracting 5-Year MOP clusters."""

    HDB_RESALE_RESOURCE_ID = "hdb_resale_flat_prices"

    async def fetch_data(self, sample_size: int = 150) -> list[dict[str, Any]]:
        """Fetch HDB resale records from data.gov.sg or fallback to synthetic generation."""
        try:
            records = await self.fetch_datastore_records(
                self.HDB_RESALE_RESOURCE_ID, limit=sample_size
            )
            if records:
                logger.info(f"Fetched {len(records)} live HDB resale records.")
                return records
        except Exception as exc:
            logger.warning(f"Failed to fetch live HDB resale dataset: {exc}")

        logger.info("Using synthetic HDB resale and MOP cluster dataset.")
        return CEASyntheticGenerator.generate_hdb_resale_and_mop(count=sample_size)
