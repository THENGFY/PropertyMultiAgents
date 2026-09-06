import time
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent2_ad_scraper.ad_parser import AdCreativeParser
from app.agents.agent2_ad_scraper.meta_ad_client import MetaAdLibraryClient
from app.agents.agent3_whitespace.analyzer import WhitespaceAnalyzer
from app.core.database import get_db
from app.models.ad_campaign import AdCampaign
from app.models.agent import AgentProfile
from app.models.whitespace_opportunity import WhitespaceOpportunity
from app.schemas.ad_intelligence import (
    AdAnalysisTriggerResponse,
    AdCampaignItem,
    AdCampaignsListResponse,
    WhitespaceOpportunitiesResponse,
    WhitespaceOpportunityItem,
)

router = APIRouter(tags=["Ad Intelligence & Whitespace Engine"])


@router.get("/ad-intelligence/campaigns", response_model=AdCampaignsListResponse)
async def get_ad_campaigns(
    district: str | None = Query(None, description="Filter by district (e.g. D10, D19)"),
    segment: str | None = Query(None, description="Filter by segment (e.g. UPGRADER, NEW_SALE, RESALE)"),
    hook: str | None = Query(None, description="Filter by detected hook (e.g. UPGRADER_MOP, TOP_SCHOOL)"),
    is_active: bool = Query(True, description="Filter by active campaigns"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve indexed Meta Ad Library campaigns run by top agents with detected marketing hooks."""
    query = select(AdCampaign).where(AdCampaign.is_active == is_active)

    if district:
        query = query.where(AdCampaign.target_district == district.strip().upper())
    if segment:
        query = query.where(AdCampaign.target_segment == segment.strip().upper())

    query = query.order_by(AdCampaign.start_date.desc()).limit(limit).offset(offset)
    results = (await db.execute(query)).scalars().all()

    # Filter hook if specified
    if hook:
        results = [r for r in results if r.detected_hooks and hook.upper() in [h.upper() for h in r.detected_hooks]]

    # Compute hook distribution
    all_ads_query = select(AdCampaign).where(AdCampaign.is_active == True)
    all_ads = (await db.execute(all_ads_query)).scalars().all()

    distribution: dict[str, int] = {}
    for ad in all_ads:
        if ad.detected_hooks:
            for h in ad.detected_hooks:
                distribution[h] = distribution.get(h, 0) + 1

    return AdCampaignsListResponse(
        total_campaigns=len(results),
        active_campaigns_count=len(all_ads),
        hook_distribution=distribution,
        campaigns=[AdCampaignItem.model_validate(r) for r in results],
    )


@router.get("/ad-intelligence/whitespace-opportunities", response_model=WhitespaceOpportunitiesResponse)
async def get_whitespace_opportunities(
    target_type: str | None = Query(None, description="Filter by target type: 'MOP_PRECINCT', 'DISTRICT'"),
    min_score: float = Query(50.0, ge=0.0, le=100.0, description="Minimum Whitespace Opportunity Score"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve high-ROI whitespace opportunities sorted by Whitespace Score ($0-100$)."""
    query = select(WhitespaceOpportunity).where(WhitespaceOpportunity.whitespace_score >= min_score)

    if target_type:
        query = query.where(WhitespaceOpportunity.target_type == target_type.strip().upper())

    query = query.order_by(WhitespaceOpportunity.whitespace_score.desc()).limit(limit).offset(offset)
    results = (await db.execute(query)).scalars().all()

    high_roi_query = select(func.count(WhitespaceOpportunity.id)).where(
        WhitespaceOpportunity.whitespace_score >= 70.0
    )
    high_roi_count = (await db.execute(high_roi_query)).scalar_one()

    return WhitespaceOpportunitiesResponse(
        total_opportunities=len(results),
        high_roi_count=high_roi_count,
        snapshot_date=date.today(),
        opportunities=[WhitespaceOpportunityItem.model_validate(r) for r in results],
    )


@router.post("/ad-intelligence/analyze", response_model=AdAnalysisTriggerResponse)
async def trigger_ad_and_whitespace_analysis(
    sample_agent_limit: int = Query(25, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Scrape/synthesize active ads for top agents and recalculate Whitespace Opportunity Scores."""
    start_time = time.perf_counter()

    # 1. Fetch top agents from Agent 1
    agents_res = await db.execute(
        select(AgentProfile).limit(sample_agent_limit)
    )
    top_agents = agents_res.scalars().all()

    if not top_agents:
        raise HTTPException(
            status_code=400,
            detail="No agent profiles found. Please run Agent 1 Ingestion first (/api/v1/ingest/trigger).",
        )

    # 2. Fetch/generate active ad campaigns via Agent 2
    ad_client = MetaAdLibraryClient()
    ads_ingested_count = 0

    existing_ads_res = await db.execute(select(AdCampaign.ad_archive_id))
    existing_ad_ids = set(existing_ads_res.scalars().all())

    for agent in top_agents:
        raw_ads = await ad_client.fetch_active_ads_for_agent(
            agent_name=agent.agent_name,
            cea_reg_no=agent.cea_reg_no,
            limit=3,
        )
        for raw in raw_ads:
            parsed = AdCreativeParser.parse_ad_record(raw=raw, agent_id=agent.id)
            if parsed["ad_archive_id"] not in existing_ad_ids:
                ad_obj = AdCampaign(
                    agent_id=parsed["agent_id"],
                    ad_archive_id=parsed["ad_archive_id"],
                    page_name=parsed["page_name"],
                    ad_headline=parsed["ad_headline"],
                    ad_body=parsed["ad_body"],
                    cta_type=parsed["cta_type"],
                    media_type=parsed["media_type"],
                    target_segment=parsed["target_segment"],
                    target_district=parsed["target_district"],
                    start_date=date.fromisoformat(parsed["start_date"]) if parsed.get("start_date") else date.today(),
                    is_active=parsed["is_active"],
                    detected_hooks=parsed["detected_hooks"],
                )
                db.add(ad_obj)
                existing_ad_ids.add(parsed["ad_archive_id"])
                ads_ingested_count += 1

    await db.commit()

    # 3. Compute Whitespace Opportunities via Agent 3
    analyzer = WhitespaceAnalyzer(session=db)
    opportunities = await analyzer.compute_whitespace_opportunities(snapshot_date=date.today())

    duration_ms = (time.perf_counter() - start_time) * 1000

    return AdAnalysisTriggerResponse(
        status="success",
        ads_ingested=ads_ingested_count,
        whitespace_opportunities_computed=len(opportunities),
        duration_ms=round(duration_ms, 2),
        message=f"Phase 2 analysis completed: Indexed {ads_ingested_count} new ads and identified {len(opportunities)} whitespace opportunities.",
    )
