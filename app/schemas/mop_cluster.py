from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class HDBMOPClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    town: str
    street_name: str
    block: str
    lease_commence_year: int
    mop_completion_year: int
    is_mop_upgrader_cohort: bool
    estimated_units: int
    median_resale_psf: float
    created_at: datetime


class HDBMOPClusterListResponse(BaseModel):
    total_clusters: int
    total_estimated_upgrader_units: int
    mop_year_filter: int | None = None
    town_filter: str | None = None
    clusters: list[HDBMOPClusterResponse]
