from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentProfile
from app.models.snapshot import AgentRankSnapshot
from app.models.transaction import AgentTransaction
from app.pipeline.aggregator import AggregationPipeline
from app.pipeline.cleaner import DataCleaner
from app.schemas.raw import RawCEASalespersonPayload, RawCEATransactionPayload


# ---------------------------------------------------------
# Action Item 1: Schema Contract Hardening & Payload Tests
# ---------------------------------------------------------
def test_raw_schema_contract_validation():
    # Test valid payload with extra unexpected keys
    raw_agent = {
        "salesperson_name": "Tan Wei Ming",
        "registration_no": "R012345A",
        "estate_agent_name": "PROPEXCELLENCE PTE LTD",
        "estate_agent_licence_no": "L3008022J",
        "telephone": "+65 91234567",
        "extra_unexpected_field": "ignore_me",
        "nested_meta": {"some": "data"},
    }
    validated = RawCEASalespersonPayload.model_validate(raw_agent)
    assert validated.salesperson_name == "Tan Wei Ming"
    assert validated.registration_no == "R012345A"

    # Test transaction with nulls and alias field
    raw_tx = {
        "salesperson_registration_no": "R012345A",
        "transaction_date_month": "2024-05",
        "type_of_transaction": "DEVELOPER SALE",
        "property_type": "EXECUTIVE_CONDOMINIUM",
        "district": None,
        "town": "TAMPINES",
        "extra_key": 12345,
    }
    validated_tx = RawCEATransactionPayload.model_validate(raw_tx)
    assert validated_tx.salesperson_registration_no == "R012345A"
    assert validated_tx.transaction_date == "2024-05"


# ---------------------------------------------------------
# Action Item 2: Ranking Mathematics & Percentile Formulation
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_tie_aware_percentile_formulation(db_session: AsyncSession):
    pipeline = AggregationPipeline(session=db_session)
    today = date.today()

    # 4 Agents: Agent A (10 txs), Agent B (10 txs - TIED #1), Agent C (5 txs - #3), Agent D (0 txs - #4)
    agents = [
        {"cea_reg_no": f"R00000{i}A", "agent_name": f"Agent {chr(65+i)}", "agency_licence_no": "L3008022J", "agency_name": "PROPEXCELLENCE", "status": "ACTIVE"}
        for i in range(4)
    ]
    txs = []
    # Agent A: 10 txs
    for j in range(10):
        txs.append({"cea_reg_no": "R000000A", "transaction_ref": f"TX-A-{j}", "transaction_date": today.isoformat(), "transaction_type": "RESALE", "property_type": "HDB_4_ROOM"})
    # Agent B: 10 txs (Tied for #1)
    for j in range(10):
        txs.append({"cea_reg_no": "R000001A", "transaction_ref": f"TX-B-{j}", "transaction_date": today.isoformat(), "transaction_type": "RESALE", "property_type": "HDB_4_ROOM"})
    # Agent C: 5 txs (Rank 3)
    for j in range(5):
        txs.append({"cea_reg_no": "R000002A", "transaction_ref": f"TX-C-{j}", "transaction_date": today.isoformat(), "transaction_type": "RESALE", "property_type": "HDB_4_ROOM"})
    # Agent D: 0 txs (Rank 4)

    await pipeline.sync_raw_data(raw_agents=agents, raw_transactions=txs)
    await pipeline.compute_and_save_rankings(snapshot_date=today, trailing_months=12)

    snapshots = (
        await db_session.execute(
            select(AgentRankSnapshot)
            .join(AgentProfile)
            .where(
                AgentRankSnapshot.snapshot_date == today,
                AgentRankSnapshot.segment == "resale",
                AgentRankSnapshot.property_category == "ALL",
            )
            .order_by(AgentRankSnapshot.rank_position.asc())
        )
    ).scalars().all()

    # Verify Competition Rank & Percentile:
    # 4 agents: Rank 1 -> 25.0%, Rank 1 -> 25.0%, Rank 3 -> 75.0%, Rank 4 -> 100.0%
    ranks = [s.rank_position for s in snapshots]
    percentiles = [s.percentile for s in snapshots]

    assert ranks == [1, 1, 3, 4]
    assert percentiles[0] == 25.0
    assert percentiles[1] == 25.0
    assert percentiles[2] == 75.0
    assert percentiles[3] == 100.0


# ---------------------------------------------------------
# Action Item 3: Secondary Segmentation (Property Category)
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_secondary_segmentation_endpoint(async_client: AsyncClient):
    # Ingest data
    await async_client.post("/api/v1/ingest/trigger", json={"sample_size": 25, "use_fixtures": True})

    # 1. Query Overall Leaderboard
    all_resp = await async_client.get("/api/v1/agent-rankings?segment=overall&property_category=all&limit=5")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert all_data["property_category"] == "ALL"

    # 2. Query HDB Category Only
    hdb_resp = await async_client.get("/api/v1/agent-rankings?segment=resale&property_category=hdb&limit=5")
    assert hdb_resp.status_code == 200
    hdb_data = hdb_resp.json()
    assert hdb_data["property_category"] == "HDB"
    assert len(hdb_data["items"]) <= 5

    # 3. Query Landed Category Only
    landed_resp = await async_client.get("/api/v1/agent-rankings?segment=new_sale&property_category=landed&limit=5")
    assert landed_resp.status_code == 200
    landed_data = landed_resp.json()
    assert landed_data["property_category"] == "LANDED"

    # 4. Invalid Category Validation
    invalid_resp = await async_client.get("/api/v1/agent-rankings?segment=resale&property_category=spaceship")
    assert invalid_resp.status_code == 400
    assert "Invalid property_category" in invalid_resp.json()["detail"]


# ---------------------------------------------------------
# Action Item 4: Database Dialect Parity Verification
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_database_dialect_parity(db_session: AsyncSession):
    # Test compound unique constraint & upsert logic
    pipeline = AggregationPipeline(session=db_session)
    agent = {
        "cea_reg_no": "R012399A",
        "agent_name": "Parity Test Agent",
        "agency_licence_no": "L3008022J",
        "agency_name": "PROPEXCELLENCE",
        "status": "ACTIVE",
    }
    tx = {
        "cea_reg_no": "R012399A",
        "transaction_ref": "TX-PARITY-1",
        "transaction_date": "2024-06-01",
        "transaction_type": "RESALE",
        "property_type": "TERRACE_HOUSE",
    }

    # Initial Insert
    res1 = await pipeline.sync_raw_data([agent], [tx])
    assert res1["transactions_count"] == 1

    # Verify property_category was correctly assigned to LANDED
    db_tx = (await db_session.execute(select(AgentTransaction).where(AgentTransaction.transaction_ref == "TX-PARITY-1"))).scalar_one()
    assert db_tx.property_category == "LANDED"

    # Duplicate Sync (Ensures composite unique constraint behaves identically)
    res2 = await pipeline.sync_raw_data([agent], [tx])
    assert res2["transactions_count"] == 0
