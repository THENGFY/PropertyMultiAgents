from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class AdCampaignItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    ad_archive_id: str
    page_name: str
    ad_headline: str
    ad_body: str
    cta_type: str
    media_type: str
    target_segment: str
    target_district: str
    start_date: date
    is_active: bool
    detected_hooks: list[str] | None = None
    created_at: datetime


class AdCampaignsListResponse(BaseModel):
    total_campaigns: int
    active_campaigns_count: int
    hook_distribution: dict[str, int]
    campaigns: list[AdCampaignItem]


class WhitespaceOpportunityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_type: str
    target_identifier: str
    district: str
    property_category: str
    market_demand_index: float
    ad_competition_index: float
    whitespace_score: float
    recommended_persona: str
    recommended_hook_angle: str
    estimated_target_units: int
    snapshot_date: date
    created_at: datetime


class WhitespaceOpportunitiesResponse(BaseModel):
    total_opportunities: int
    high_roi_count: int
    snapshot_date: date
    opportunities: list[WhitespaceOpportunityItem]


class AdAnalysisTriggerResponse(BaseModel):
    status: str
    ads_ingested: int
    whitespace_opportunities_computed: int
    duration_ms: float
    message: str
