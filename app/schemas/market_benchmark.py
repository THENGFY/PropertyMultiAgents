from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class MarketPriceBenchmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    district: str
    town: str
    market_segment: str
    property_category: str
    snapshot_date: date
    median_psf: float
    p25_psf: float
    p75_psf: float
    median_quantum: float
    quarterly_volume: int
    created_at: datetime


class MarketPriceBenchmarkListResponse(BaseModel):
    total_benchmarks: int
    district_filter: str | None = None
    segment_filter: str | None = None
    benchmarks: list[MarketPriceBenchmarkResponse]
