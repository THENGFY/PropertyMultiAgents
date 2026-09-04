import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "stats" in data


@pytest.mark.asyncio
async def test_ingest_and_rankings_flow(async_client: AsyncClient):
    # 1. Trigger ingestion
    ingest_resp = await async_client.post(
        "/api/v1/ingest/trigger",
        json={"sample_size": 20, "use_fixtures": True},
    )
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert ingest_data["status"] == "success"
    assert ingest_data["agents_ingested"] == 20

    # 2. Query Rankings for Overall
    rank_resp = await async_client.get("/api/v1/agent-rankings?segment=overall&limit=10")
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert rank_data["segment"] == "overall"
    assert len(rank_data["items"]) <= 10
    assert rank_data["total_cohort_size"] == 20

    first_agent = rank_data["items"][0]
    assert first_agent["rank"] == 1
    assert "cea_reg_no" in first_agent
    assert "agency_name" in first_agent

    # 3. Query Individual Agent Details
    agent_cea = first_agent["cea_reg_no"]
    agent_resp = await async_client.get(f"/api/v1/agents/{agent_cea}")
    assert agent_resp.status_code == 200
    agent_detail = agent_resp.json()
    assert agent_detail["cea_reg_no"] == agent_cea
    assert "agency" in agent_detail
    assert "rankings" in agent_detail
    assert "overall" in agent_detail["rankings"]


@pytest.mark.asyncio
async def test_invalid_segment_validation(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/agent-rankings?segment=invalid_segment")
    assert resp.status_code == 400
    assert "Invalid segment" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_agent_not_found(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/agents/R0000000X")
    assert resp.status_code == 404
