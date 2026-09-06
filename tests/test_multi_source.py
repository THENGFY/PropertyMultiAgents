import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.ingestion.adapters import HDBResaleAdapter, URAPMIAdapter, OneMapGeoAdapter
from app.ingestion.cea_client import CEAClient
from app.pipeline.aggregator import AggregationPipeline
from app.models.mop_cluster import HDBMOPCluster
from app.models.market_benchmark import MarketPriceBenchmark


@pytest.mark.asyncio
async def test_hdb_resale_adapter_synthetic_generation():
    adapter = HDBResaleAdapter()
    records = await adapter.fetch_data(sample_size=25)
    assert len(records) == 25
    assert "town" in records[0]
    assert "mop_year" in records[0]
    assert "resale_price" in records[0]


@pytest.mark.asyncio
async def test_ura_pmi_adapter_synthetic_generation():
    adapter = URAPMIAdapter()
    records = await adapter.fetch_data(sample_size=30)
    assert len(records) == 30
    assert "project_name" in records[0]
    assert "unit_price_psf" in records[0]
    assert "market_segment" in records[0]


@pytest.mark.asyncio
async def test_onemap_geo_adapter():
    adapter = OneMapGeoAdapter()
    records = await adapter.fetch_data(sample_size=15)
    assert len(records) == 15
    assert "nearest_top_school" in records[0]
    assert "transit_score" in records[0]


@pytest.mark.asyncio
async def test_multi_source_ingestion_and_endpoints(
    async_client: AsyncClient, db_session: AsyncSession
):
    # 1. Trigger full multi-source ingestion
    resp = await async_client.post(
        "/api/v1/ingest/trigger",
        json={"use_fixtures": True, "sample_size": 30},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["agencies_ingested"] > 0
    assert data["agents_ingested"] > 0

    # 2. Test HDB MOP clusters endpoint
    mop_resp = await async_client.get("/api/v1/hdb/mop-clusters?limit=50&upgrader_cohort_only=false")
    assert mop_resp.status_code == 200
    mop_data = mop_resp.json()
    assert mop_data["total_clusters"] > 0
    assert len(mop_data["clusters"]) > 0
    assert "mop_completion_year" in mop_data["clusters"][0]

    # 3. Test Market benchmarks endpoint
    bench_resp = await async_client.get("/api/v1/market-benchmarks?limit=50")
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()
    assert bench_data["total_benchmarks"] > 0
    assert len(bench_data["benchmarks"]) > 0
    assert "median_psf" in bench_data["benchmarks"][0]

    # 4. Test Health endpoint includes multi-source stats
    health_resp = await async_client.get("/api/v1/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "healthy"
    assert health_data["stats"]["hdb_mop_clusters"] > 0
    assert health_data["stats"]["market_price_benchmarks"] > 0
