from datetime import date, timedelta
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.synthetic_data import CEASyntheticGenerator
from app.models.agent import AgentProfile
from app.models.snapshot import AgentRankSnapshot
from app.pipeline.aggregator import AggregationPipeline


@pytest.mark.asyncio
async def test_pipeline_sync_and_rankings(db_session: AsyncSession):
    pipeline = AggregationPipeline(session=db_session)

    # Generate synthetic dataset
    agents = CEASyntheticGenerator.generate_agents(count=10, seed=123)
    txs = CEASyntheticGenerator.generate_transactions(agents=agents, seed=123)

    # 1. Test Sync
    stats = await pipeline.sync_raw_data(raw_agents=agents, raw_transactions=txs)
    assert stats["agents_count"] == 10
    assert stats["transactions_count"] > 0

    # Verify agent records in DB
    db_agents = (await db_session.execute(select(AgentProfile))).scalars().all()
    assert len(db_agents) == 10

    # 2. Test Idempotency (Re-sync same data should not duplicate)
    stats_repeat = await pipeline.sync_raw_data(raw_agents=agents, raw_transactions=txs)
    assert stats_repeat["agents_count"] == 10
    assert stats_repeat["transactions_count"] == 0  # 0 new duplicates inserted

    # 3. Test Rankings Computation
    today = date.today()
    snapshots_count = await pipeline.compute_and_save_rankings(snapshot_date=today, trailing_months=12)
    # 10 agents * 4 segments * 5 property categories = 200 snapshots
    assert snapshots_count == 200

    # Verify snapshot properties
    overall_snapshots = (
        await db_session.execute(
            select(AgentRankSnapshot)
            .where(
                AgentRankSnapshot.snapshot_date == today,
                AgentRankSnapshot.segment == "overall",
                AgentRankSnapshot.property_category == "ALL",
            )
            .order_by(AgentRankSnapshot.rank_position.asc())
        )
    ).scalars().all()

    assert len(overall_snapshots) == 10
    assert overall_snapshots[0].rank_position == 1
    assert overall_snapshots[0].percentile <= 10.0
    assert overall_snapshots[0].transaction_count >= overall_snapshots[-1].transaction_count


@pytest.mark.asyncio
async def test_t12m_boundary_filtering(db_session: AsyncSession):
    pipeline = AggregationPipeline(session=db_session)
    today = date.today()

    agent = {
        "cea_reg_no": "R099999Z",
        "agent_name": "Test Boundary Agent",
        "agency_licence_no": "L3008022J",
        "agency_name": "PROPEXCELLENCE PTE LTD",
        "status": "ACTIVE",
    }

    # 1 Tx inside T12M (30 days ago), 1 Tx outside T12M (400 days ago)
    txs = [
        {
            "cea_reg_no": "R099999Z",
            "transaction_ref": "TX-IN-1",
            "transaction_date": (today - timedelta(days=30)).isoformat(),
            "transaction_type": "RESALE",
            "property_type": "HDB",
        },
        {
            "cea_reg_no": "R099999Z",
            "transaction_ref": "TX-OUT-2",
            "transaction_date": (today - timedelta(days=400)).isoformat(),
            "transaction_type": "RESALE",
            "property_type": "HDB",
        },
    ]

    await pipeline.sync_raw_data(raw_agents=[agent], raw_transactions=txs)
    await pipeline.compute_and_save_rankings(snapshot_date=today, trailing_months=12)

    snapshot = (
        await db_session.execute(
            select(AgentRankSnapshot).where(
                AgentRankSnapshot.snapshot_date == today,
                AgentRankSnapshot.segment == "resale",
                AgentRankSnapshot.property_category == "ALL",
            )
        )
    ).scalar_one()

    # Only 1 transaction inside the T12M window should be counted
    assert snapshot.transaction_count == 1
