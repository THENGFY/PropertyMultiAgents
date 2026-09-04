import time
import pytest
from httpx import AsyncClient
from app.ingestion.synthetic_data import CEASyntheticGenerator
from app.pipeline.aggregator import AggregationPipeline
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_api_latency_benchmark(async_client: AsyncClient):
    # 1. Ingest cohort
    await async_client.post(
        "/api/v1/ingest/trigger",
        json={"sample_size": 100, "use_fixtures": True},
    )

    # 2. Benchmark 50 consecutive queries to /api/v1/agent-rankings
    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = await async_client.get("/api/v1/agent-rankings?segment=overall&limit=25")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"\n[BENCHMARK] Ranking Endpoint Latency: P50={p50:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")

    # SLA assertion: P95 must be under 50ms
    assert p95 < 50.0, f"P95 latency {p95}ms exceeded 50ms SLA"


@pytest.mark.asyncio
async def test_large_volume_pipeline_performance(db_session: AsyncSession):
    pipeline = AggregationPipeline(session=db_session)
    
    # 200 agents, ~3000 transactions
    agents = CEASyntheticGenerator.generate_agents(count=200, seed=999)
    txs = CEASyntheticGenerator.generate_transactions(agents=agents, seed=999)

    t0 = time.perf_counter()
    stats = await pipeline.sync_raw_data(raw_agents=agents, raw_transactions=txs)
    sync_time = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    snapshots_count = await pipeline.compute_and_save_rankings()
    calc_time = (time.perf_counter() - t1) * 1000

    print(f"\n[BENCHMARK] Volume Sync: {stats['transactions_count']} txs in {sync_time:.2f}ms | Ranking: {snapshots_count} snapshots in {calc_time:.2f}ms")
    assert stats["agents_count"] == 200
    assert snapshots_count == 4000  # 200 agents * 4 segments * 5 property categories
