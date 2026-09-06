import logging
from typing import Any
from app.ingestion.adapters.base import BaseDatasetAdapter
from app.ingestion.synthetic_data import CEASyntheticGenerator

logger = logging.getLogger(__name__)


class OneMapGeoAdapter(BaseDatasetAdapter):
    """Adapter for geocoding and computing school catchment & transport scores via SLA OneMap."""

    def __init__(self, base_url: str | None = None):
        super().__init__(base_url=base_url or "https://www.onemap.gov.sg/api/common/elastic/search")

    async def fetch_data(self, sample_size: int = 50) -> list[dict[str, Any]]:
        """Fetch geocoding benchmarks or fallback to synthetic geospatial data."""
        return CEASyntheticGenerator.generate_geospatial_benchmarks(count=sample_size)
