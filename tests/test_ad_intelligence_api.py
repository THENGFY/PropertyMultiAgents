import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_phase2_full_ad_intelligence_pipeline(
    async_client: AsyncClient, db_session: AsyncSession
):
    # 1. First run Agent 1 ingestion so top agents exist in database
    init_resp = await async_client.post(
        "/api/v1/ingest/trigger",
        json={"use_fixtures": True, "sample_size": 25},
    )
    assert init_resp.status_code == 200

    # 2. Trigger Phase 2 Ad Analysis
    analyze_resp = await async_client.post("/api/v1/ad-intelligence/analyze?sample_agent_limit=15")
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.json()
    assert analyze_data["status"] == "success"
    assert analyze_data["ads_ingested"] > 0
    assert analyze_data["whitespace_opportunities_computed"] > 0

    # 3. Test GET ad campaigns endpoint
    campaigns_resp = await async_client.get("/api/v1/ad-intelligence/campaigns?limit=50")
    assert campaigns_resp.status_code == 200
    camp_data = campaigns_resp.json()
    assert camp_data["total_campaigns"] > 0
    assert len(camp_data["campaigns"]) > 0
    assert "ad_headline" in camp_data["campaigns"][0]
    assert "detected_hooks" in camp_data["campaigns"][0]

    # 4. Test GET whitespace opportunities endpoint
    ws_resp = await async_client.get("/api/v1/ad-intelligence/whitespace-opportunities?min_score=0")
    assert ws_resp.status_code == 200
    ws_data = ws_resp.json()
    assert ws_data["total_opportunities"] > 0
    assert len(ws_data["opportunities"]) > 0
    top_opp = ws_data["opportunities"][0]
    assert "whitespace_score" in top_opp
    assert "recommended_hook_angle" in top_opp
    assert top_opp["whitespace_score"] >= 0
