import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent3_whitespace.analyzer import WhitespaceAnalyzer
from app.agents.agent3_whitespace.recommendation_builder import WhitespaceRecommendationBuilder
from app.models.ad_campaign import AdCampaign
from app.models.agency import Agency
from app.models.agent import AgentProfile
from app.models.market_benchmark import MarketPriceBenchmark
from app.models.mop_cluster import HDBMOPCluster


def test_whitespace_recommendation_builder():
    persona_mop, hook_mop = WhitespaceRecommendationBuilder.build_recommendation(
        target_type="MOP_PRECINCT",
        target_identifier="PUNGGOL",
        district="D19",
        property_category="HDB",
        ad_competition_count=1,
        estimated_units=450,
    )
    assert "MOP" in persona_mop
    assert "PUNGGOL" in hook_mop

    persona_ccr, hook_ccr = WhitespaceRecommendationBuilder.build_recommendation(
        target_type="DISTRICT",
        target_identifier="CCR Luxury Core",
        district="D10",
        property_category="CONDO_APT",
        ad_competition_count=0,
        estimated_units=150,
    )
    assert "Wealth" in persona_ccr or "Cash" in persona_ccr
    assert "D10" in hook_ccr


@pytest.mark.asyncio
async def test_whitespace_analyzer_computation(db_session: AsyncSession):
    # 1. Setup agency and agent
    agency = Agency(licence_no="L3008022J", agency_name="TEST AGENCY")
    db_session.add(agency)
    await db_session.flush()

    agent = AgentProfile(
        cea_reg_no="R0999999A",
        agent_name="Agent Tester",
        agency_id=agency.id,
        status="ACTIVE",
    )
    db_session.add(agent)
    await db_session.flush()

    # 2. Add HDB MOP cluster
    mop = HDBMOPCluster(
        town="PUNGGOL",
        street_name="PUNGGOL FIELD",
        block="101A",
        lease_commence_year=2020,
        mop_completion_year=2025,
        is_mop_upgrader_cohort=True,
        estimated_units=300,
        median_resale_psf=600.0,
    )
    db_session.add(mop)

    # 3. Add Market Price Benchmark
    bench = MarketPriceBenchmark(
        district="D10",
        town="BUKIT TIMAH",
        market_segment="CCR",
        property_category="CONDO_APT",
        snapshot_date=date.today(),
        median_psf=2900.0,
        p25_psf=2700.0,
        p75_psf=3100.0,
        median_quantum=2700000.0,
        quarterly_volume=40,
    )
    db_session.add(bench)
    await db_session.commit()

    # 4. Compute Whitespace
    analyzer = WhitespaceAnalyzer(session=db_session)
    opps = await analyzer.compute_whitespace_opportunities()

    assert len(opps) >= 2
    for opp in opps:
        assert opp.whitespace_score >= 0.0
        assert opp.whitespace_score <= 100.0
        assert opp.recommended_persona != ""
        assert opp.recommended_hook_angle != ""


@pytest.mark.asyncio
async def test_subzone_level_whitespace_competition_separation(db_session: AsyncSession):
    # 1. Setup agency and agent
    agency = Agency(licence_no="L3008022J", agency_name="TEST AGENCY")
    db_session.add(agency)
    await db_session.flush()

    agent = AgentProfile(
        cea_reg_no="R0888888B",
        agent_name="Agent Subzone Tester",
        agency_id=agency.id,
        status="ACTIVE",
    )
    db_session.add(agent)
    await db_session.flush()

    # 2. Add two distinct MOP clusters in District D19: PUNGGOL and SENGKANG
    mop_punggol = HDBMOPCluster(
        town="PUNGGOL",
        street_name="PUNGGOL CENTRAL",
        block="201A",
        lease_commence_year=2020,
        mop_completion_year=2025,
        is_mop_upgrader_cohort=True,
        estimated_units=500,
        median_resale_psf=620.0,
    )
    mop_sengkang = HDBMOPCluster(
        town="SENGKANG",
        street_name="COMPASSVALE ROAD",
        block="301A",
        lease_commence_year=2020,
        mop_completion_year=2025,
        is_mop_upgrader_cohort=True,
        estimated_units=500,
        median_resale_psf=590.0,
    )
    db_session.add_all([mop_punggol, mop_sengkang])

    # 3. Add active ad campaign targeting explicitly SENGKANG only
    ad_sengkang = AdCampaign(
        agent_id=agent.id,
        ad_archive_id="AD-SENGKANG-ONLY-1",
        page_name="Sengkang Specialist",
        ad_headline="Sengkang MOP Reached! Upgrade now",
        ad_body="Exclusive Sengkang Compassvale upgrade roadmap.",
        cta_type="LEARN_MORE",
        media_type="IMAGE",
        target_segment="UPGRADER",
        target_district="D19",
        start_date=date.today(),
        is_active=True,
        detected_hooks=["UPGRADER_MOP"],
    )
    db_session.add(ad_sengkang)
    await db_session.commit()

    analyzer = WhitespaceAnalyzer(session=db_session)
    opps = await analyzer.compute_whitespace_opportunities()

    opp_map = {o.target_identifier: o for o in opps}
    assert "PUNGGOL MOP Cluster" in opp_map
    assert "SENGKANG MOP Cluster" in opp_map

    # Punggol should have higher whitespace score (less competition) than Sengkang
    punggol_score = opp_map["PUNGGOL MOP Cluster"].whitespace_score
    sengkang_score = opp_map["SENGKANG MOP Cluster"].whitespace_score
    assert punggol_score > sengkang_score

