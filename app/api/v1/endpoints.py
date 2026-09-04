import time
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.ingestion.cea_client import CEAClient
from app.models.agency import Agency
from app.models.agent import AgentProfile
from app.models.snapshot import AgentRankSnapshot
from app.models.transaction import AgentTransaction
from app.pipeline.aggregator import AggregationPipeline
from app.schemas.ranking import (
    IngestTriggerRequest,
    IngestTriggerResponse,
    RankedAgentItem,
    RankedAgentsResponse,
)

router = APIRouter(tags=["Agent Rankings & Ingestion"])


@router.get("/agent-rankings", response_model=RankedAgentsResponse)
async def get_agent_rankings(
    segment: str = Query(
        "overall",
        description="Market segment: 'overall', 'new_sale', 'resale', 'rental'",
    ),
    property_category: str = Query(
        "all",
        description="Property category: 'all', 'hdb', 'condo_apt', 'landed', 'commercial'",
    ),
    snapshot_date: date | None = Query(
        None, description="Date of ranking snapshot (defaults to latest available)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of agents to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve top-ranked agents by transaction volume for a specific segment and optional property category."""
    norm_segment = segment.lower().strip()
    valid_segments = ["overall", "new_sale", "resale", "rental"]
    if norm_segment not in valid_segments:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid segment '{segment}'. Must be one of {valid_segments}",
        )

    # Normalize property category
    norm_category = property_category.upper().strip()
    if norm_category in ["PRIVATE_RESIDENTIAL", "CONDO", "APARTMENT"]:
        norm_category = "CONDO_APT"
    valid_categories = ["ALL", "HDB", "CONDO_APT", "LANDED", "COMMERCIAL"]
    if norm_category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid property_category '{property_category}'. Must be one of {valid_categories}",
        )

    # 1. Determine snapshot date if not provided
    if not snapshot_date:
        latest_date_query = select(func.max(AgentRankSnapshot.snapshot_date)).where(
            AgentRankSnapshot.segment == norm_segment,
            AgentRankSnapshot.property_category == norm_category,
        )
        latest_date_res = await db.execute(latest_date_query)
        snapshot_date = latest_date_res.scalar_one_or_none()

    if not snapshot_date:
        return RankedAgentsResponse(
            segment=norm_segment,
            property_category=norm_category,
            snapshot_date=date.today(),
            trailing_window_months=12,
            total_cohort_size=0,
            limit=limit,
            offset=offset,
            items=[],
        )

    # 2. Query total cohort size for this snapshot, segment & category
    total_query = select(func.count(AgentRankSnapshot.id)).where(
        AgentRankSnapshot.snapshot_date == snapshot_date,
        AgentRankSnapshot.segment == norm_segment,
        AgentRankSnapshot.property_category == norm_category,
    )
    total_cohort = (await db.execute(total_query)).scalar_one()

    # 3. Query ranked snapshot items joining agent & agency
    query = (
        select(AgentRankSnapshot)
        .options(
            selectinload(AgentRankSnapshot.agent).selectinload(AgentProfile.agency),
            selectinload(AgentRankSnapshot.agent).selectinload(AgentProfile.rank_snapshots),
        )
        .where(
            AgentRankSnapshot.snapshot_date == snapshot_date,
            AgentRankSnapshot.segment == norm_segment,
            AgentRankSnapshot.property_category == norm_category,
        )
        .order_by(AgentRankSnapshot.rank_position.asc())
        .limit(limit)
        .offset(offset)
    )

    results = (await db.execute(query)).scalars().all()

    items: list[RankedAgentItem] = []
    for snap in results:
        agent = snap.agent
        agency = agent.agency if agent else None

        # Extract breakdown from agent's snapshots on this date for this category
        counts = {"new_sale": 0, "resale": 0, "rental": 0}
        if agent and agent.rank_snapshots:
            for s in agent.rank_snapshots:
                if (
                    s.snapshot_date == snapshot_date
                    and s.property_category == norm_category
                    and s.segment in counts
                ):
                    counts[s.segment] = s.transaction_count

        items.append(
            RankedAgentItem(
                rank=snap.rank_position,
                percentile=snap.percentile,
                agent_id=snap.agent_id,
                cea_reg_no=agent.cea_reg_no if agent else "UNKNOWN",
                agent_name=agent.agent_name if agent else "UNKNOWN",
                agency_name=agency.agency_name if agency else "INDEPENDENT",
                agency_licence=agency.licence_no if agency else "L0000000Z",
                segment=snap.segment,
                property_category=snap.property_category,
                transaction_count=snap.transaction_count,
                new_sale_count=counts["new_sale"],
                resale_count=counts["resale"],
                rental_count=counts["rental"],
                snapshot_date=snap.snapshot_date,
            )
        )

    return RankedAgentsResponse(
        segment=norm_segment,
        property_category=norm_category,
        snapshot_date=snapshot_date,
        trailing_window_months=12,
        total_cohort_size=total_cohort,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/agents/{cea_reg_no}")
async def get_agent_details(
    cea_reg_no: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed agent profile, agency info, and rank snapshots."""
    cleaned_reg = cea_reg_no.strip().upper()
    query = (
        select(AgentProfile)
        .options(
            selectinload(AgentProfile.agency),
            selectinload(AgentProfile.rank_snapshots),
            selectinload(AgentProfile.transactions),
        )
        .where(AgentProfile.cea_reg_no == cleaned_reg)
    )
    res = await db.execute(query)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with CEA registration number '{cea_reg_no}' not found.",
        )

    # Compile rankings
    rankings = {}
    for r in agent.rank_snapshots:
        rankings[r.segment] = {
            "snapshot_date": r.snapshot_date.isoformat(),
            "rank": r.rank_position,
            "percentile": r.percentile,
            "transactions_count": r.transaction_count,
        }

    return {
        "id": agent.id,
        "cea_reg_no": agent.cea_reg_no,
        "agent_name": agent.agent_name,
        "contact_number": agent.contact_number,
        "status": agent.status,
        "registration_start_date": agent.registration_start_date.isoformat()
        if agent.registration_start_date
        else None,
        "agency": {
            "id": agent.agency.id if agent.agency else None,
            "agency_name": agent.agency.agency_name if agent.agency else "INDEPENDENT",
            "licence_no": agent.agency.licence_no if agent.agency else "L0000000Z",
        },
        "rankings": rankings,
        "total_historical_transactions": len(agent.transactions),
    }


@router.post("/ingest/trigger", response_model=IngestTriggerResponse)
async def trigger_ingestion_and_aggregation(
    payload: IngestTriggerRequest = IngestTriggerRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Trigger on-demand data ingestion worker from data.gov.sg / fixtures and re-compute rankings."""
    start_time = time.perf_counter()

    client = CEAClient()
    raw_agents, raw_txs = await client.ingest_raw_feed(
        use_fixtures=payload.use_fixtures, sample_size=payload.sample_size
    )

    pipeline = AggregationPipeline(session=db)
    sync_stats = await pipeline.sync_raw_data(
        raw_agents=raw_agents, raw_transactions=raw_txs
    )

    ref_date = payload.snapshot_date or date.today()
    snapshots_count = await pipeline.compute_and_save_rankings(
        snapshot_date=ref_date, trailing_months=12
    )

    duration_ms = (time.perf_counter() - start_time) * 1000

    return IngestTriggerResponse(
        status="success",
        snapshot_date=ref_date,
        agencies_ingested=sync_stats["agencies_count"],
        agents_ingested=sync_stats["agents_count"],
        transactions_ingested=sync_stats["transactions_count"],
        rankings_computed=snapshots_count,
        duration_ms=round(duration_ms, 2),
        message=f"Successfully ingested {sync_stats['agents_count']} agents, {sync_stats['transactions_count']} transactions and generated {snapshots_count} rank snapshots.",
    )
