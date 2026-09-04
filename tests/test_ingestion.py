import pytest
from app.ingestion.cea_client import CEAClient
from app.ingestion.synthetic_data import CEASyntheticGenerator


@pytest.mark.asyncio
async def test_cea_synthetic_generator():
    agents = CEASyntheticGenerator.generate_agents(count=25, seed=42)
    assert len(agents) == 25
    for a in agents:
        assert a["cea_reg_no"].startswith("R0")
        assert len(a["cea_reg_no"]) == 9
        assert "agency_licence_no" in a

    txs = CEASyntheticGenerator.generate_transactions(agents=agents, seed=42)
    assert len(txs) > 25
    for tx in txs:
        assert tx["transaction_type"] in ["NEW_SALE", "RESALE", "RENTAL"]
        assert "transaction_date" in tx


@pytest.mark.asyncio
async def test_cea_client_fallback_mode():
    client = CEAClient(base_url="http://invalid-unreachable-domain-123.sg")
    agents, txs = await client.ingest_raw_feed(use_fixtures=False, sample_size=15)
    # Should gracefully fall back to synthetic data
    assert len(agents) == 15
    assert len(txs) > 0
