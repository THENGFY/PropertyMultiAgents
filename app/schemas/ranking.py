from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class RankSnapshotBase(BaseModel):
    snapshot_date: date
    segment: str  # overall, new_sale, resale, rental
    property_category: str = "ALL"  # ALL, HDB, CONDO_APT, LANDED, COMMERCIAL
    transaction_count: int
    rank_position: int
    percentile: float
    trailing_window_months: int = 12


class RankSnapshotCreate(RankSnapshotBase):
    agent_id: str


class RankSnapshotOut(RankSnapshotBase):
    id: str
    agent_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RankedAgentItem(BaseModel):
    rank: int
    percentile: float
    agent_id: str
    cea_reg_no: str
    agent_name: str
    agency_name: str
    agency_licence: str
    segment: str
    property_category: str = "ALL"
    transaction_count: int
    new_sale_count: int
    resale_count: int
    rental_count: int
    snapshot_date: date


class RankedAgentsResponse(BaseModel):
    segment: str
    property_category: str = "ALL"
    snapshot_date: date
    trailing_window_months: int
    total_cohort_size: int
    limit: int
    offset: int
    items: list[RankedAgentItem]


class IngestTriggerRequest(BaseModel):
    snapshot_date: date | None = None
    use_fixtures: bool = False
    sample_size: int = 200


class IngestTriggerResponse(BaseModel):
    status: str
    snapshot_date: date
    agencies_ingested: int
    agents_ingested: int
    transactions_ingested: int
    rankings_computed: int
    duration_ms: float
    message: str
