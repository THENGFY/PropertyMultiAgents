import logging
from typing import Any
from app.ingestion.adapters.base import BaseDatasetAdapter
from app.ingestion.synthetic_data import CEASyntheticGenerator

logger = logging.getLogger(__name__)


class URAPMIAdapter(BaseDatasetAdapter):
    """Adapter for ingesting URA Property Market Information (PMI) private residential transactions."""

    URA_PMI_RESOURCE_ID = "ura_private_residential_transactions"

    async def fetch_data(self, sample_size: int = 150) -> list[dict[str, Any]]:
        """Fetch URA private residential caveats or fallback to synthetic generation."""
        try:
            records = await self.fetch_datastore_records(
                self.URA_PMI_RESOURCE_ID, limit=sample_size
            )
            if records:
                logger.info(f"Fetched {len(records)} live URA PMI records.")
                return records
        except Exception as exc:
            logger.warning(f"Failed to fetch live URA PMI dataset: {exc}")

        logger.info("Using synthetic URA private residential caveat dataset.")
        return CEASyntheticGenerator.generate_ura_caveats(count=sample_size)
