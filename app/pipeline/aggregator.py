from datetime import date, datetime, timedelta
import logging
from typing import Any
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agency import Agency
from app.models.agent import AgentProfile
from app.models.market_benchmark import MarketPriceBenchmark
from app.models.mop_cluster import HDBMOPCluster
from app.models.snapshot import AgentRankSnapshot
from app.models.transaction import AgentTransaction
from app.pipeline.cleaner import DataCleaner

logger = logging.getLogger(__name__)



class AggregationPipeline:
    """Orchestrates cleaning, entity upserting, T12M aggregation, and ranking generation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_raw_data(
        self, raw_agents: list[dict[str, Any]], raw_transactions: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Clean and persist agencies, agent profiles, and transactions."""
        # 1. Clean agents
        cleaned_agents = []
        agencies_map: dict[str, str] = {}  # licence_no -> agency_name

        for item in raw_agents:
            cleaned = DataCleaner.clean_agent_record(item)
            if cleaned:
                cleaned_agents.append(cleaned)
                agencies_map[cleaned["agency_licence_no"]] = cleaned["agency_name"]

        # 2. Upsert Agencies
        existing_agencies_res = await self.session.execute(select(Agency))
        existing_agencies = {a.licence_no: a for a in existing_agencies_res.scalars().all()}

        for licence_no, agency_name in agencies_map.items():
            if licence_no not in existing_agencies:
                agency = Agency(licence_no=licence_no, agency_name=agency_name)
                self.session.add(agency)
                existing_agencies[licence_no] = agency

        await self.session.flush()

        # 3. Upsert Agent Profiles
        existing_agents_res = await self.session.execute(select(AgentProfile))
        existing_agents = {a.cea_reg_no: a for a in existing_agents_res.scalars().all()}

        agents_ingested_count = 0
        for ag in cleaned_agents:
            reg_no = ag["cea_reg_no"]
            agency = existing_agencies[ag["agency_licence_no"]]

            if reg_no in existing_agents:
                # Update existing profile
                agent_obj = existing_agents[reg_no]
                agent_obj.agent_name = ag["agent_name"]
                agent_obj.agency_id = agency.id
                agent_obj.contact_number = ag["contact_number"]
                agent_obj.status = ag["status"]
                agent_obj.registration_start_date = ag["registration_start_date"]
                agent_obj.registration_end_date = ag["registration_end_date"]
            else:
                agent_obj = AgentProfile(
                    cea_reg_no=reg_no,
                    agent_name=ag["agent_name"],
                    agency_id=agency.id,
                    contact_number=ag["contact_number"],
                    status=ag["status"],
                    registration_start_date=ag["registration_start_date"],
                    registration_end_date=ag["registration_end_date"],
                )
                self.session.add(agent_obj)
                existing_agents[reg_no] = agent_obj
                agents_ingested_count += 1

        await self.session.flush()

        # 4. Clean & Upsert Transactions
        cleaned_txs = []
        for tx in raw_transactions:
            cleaned = DataCleaner.clean_transaction_record(tx)
            if cleaned and cleaned["cea_reg_no"] in existing_agents:
                cleaned_txs.append(cleaned)

        tx_ingested_count = 0
        # Fetch existing transactions keys for deduplication
        existing_txs_res = await self.session.execute(
            select(AgentTransaction.agent_id, AgentTransaction.transaction_ref, AgentTransaction.transaction_date)
        )
        existing_tx_keys = set(existing_txs_res.all())

        for tx in cleaned_txs:
            agent_obj = existing_agents[tx["cea_reg_no"]]
            key = (agent_obj.id, tx["transaction_ref"], tx["transaction_date"])
            if key not in existing_tx_keys:
                tx_obj = AgentTransaction(
                    agent_id=agent_obj.id,
                    transaction_ref=tx["transaction_ref"],
                    transaction_date=tx["transaction_date"],
                    property_type=tx["property_type"],
                    property_category=tx.get("property_category", "CONDO_APT"),
                    transaction_type=tx["transaction_type"],
                    district=tx["district"],
                    town=tx["town"],
                    raw_payload=tx["raw_payload"],
                )
                self.session.add(tx_obj)
                existing_tx_keys.add(key)
                tx_ingested_count += 1

        await self.session.commit()

        return {
            "agencies_count": len(existing_agencies),
            "agents_count": len(existing_agents),
            "transactions_count": tx_ingested_count,
        }

    async def compute_and_save_rankings(
        self, snapshot_date: date | None = None, trailing_months: int = 12
    ) -> int:
        """Compute rolling trailing 12-month transaction counts and rank snapshots across segments and property categories."""
        ref_date = snapshot_date or date.today()
        window_start = ref_date - timedelta(days=trailing_months * 30.5)

        # 1. Fetch all agents
        agents_res = await self.session.execute(select(AgentProfile))
        agents = agents_res.scalars().all()
        if not agents:
            return 0

        # 2. Fetch all transactions in the T12M window
        tx_res = await self.session.execute(
            select(AgentTransaction).where(
                AgentTransaction.transaction_date >= window_start,
                AgentTransaction.transaction_date <= ref_date,
            )
        )
        transactions = tx_res.scalars().all()

        # Delete any existing snapshot records for this snapshot_date
        await self.session.execute(
            delete(AgentRankSnapshot).where(AgentRankSnapshot.snapshot_date == ref_date)
        )

        segments = ["overall", "new_sale", "resale", "rental"]
        prop_categories = ["ALL", "HDB", "CONDO_APT", "LANDED", "COMMERCIAL"]
        total_cohort = len(agents)
        snapshots_created = 0

        for category in prop_categories:
            # Filter transactions for category
            cat_txs = (
                transactions
                if category == "ALL"
                else [t for t in transactions if t.property_category == category]
            )

            # Map transactions to agents
            agent_counts: dict[str, dict[str, int]] = {
                a.id: {"overall": 0, "new_sale": 0, "resale": 0, "rental": 0}
                for a in agents
            }

            for tx in cat_txs:
                if tx.agent_id in agent_counts:
                    agent_counts[tx.agent_id]["overall"] += 1
                    t_type = tx.transaction_type.upper()
                    if t_type == "NEW_SALE":
                        agent_counts[tx.agent_id]["new_sale"] += 1
                    elif t_type == "RESALE":
                        agent_counts[tx.agent_id]["resale"] += 1
                    elif t_type == "RENTAL":
                        agent_counts[tx.agent_id]["rental"] += 1

            for segment in segments:
                # Sort agents descending by transaction count in segment
                sorted_agents = sorted(
                    agent_counts.items(),
                    key=lambda x: x[1][segment],
                    reverse=True,
                )

                # Standard Competition Ranking (1224) + Percentile Formulation
                current_rank = 1
                for idx, (agent_id, counts) in enumerate(sorted_agents):
                    count = counts[segment]
                    if idx > 0 and count < sorted_agents[idx - 1][1][segment]:
                        current_rank = idx + 1

                    percentile = round((current_rank / total_cohort) * 100, 2)

                    snapshot = AgentRankSnapshot(
                        agent_id=agent_id,
                        snapshot_date=ref_date,
                        segment=segment,
                        property_category=category,
                        transaction_count=count,
                        rank_position=current_rank,
                        percentile=percentile,
                        trailing_window_months=trailing_months,
                    )
                    self.session.add(snapshot)
                    snapshots_created += 1

        await self.session.commit()
        return snapshots_created

    async def sync_hdb_mop_clusters(self, raw_records: list[dict[str, Any]]) -> int:
        """Clean, deduplicate, and upsert HDB 5-Year MOP clusters."""
        cleaned_clusters = []
        for r in raw_records:
            cl = DataCleaner.clean_hdb_mop_record(r)
            if cl:
                cleaned_clusters.append(cl)

        if not cleaned_clusters:
            return 0

        existing_res = await self.session.execute(
            select(HDBMOPCluster.town, HDBMOPCluster.street_name, HDBMOPCluster.block, HDBMOPCluster.mop_completion_year)
        )
        existing_keys = set(existing_res.all())

        count = 0
        for item in cleaned_clusters:
            key = (item["town"], item["street_name"], item["block"], item["mop_completion_year"])
            if key not in existing_keys:
                obj = HDBMOPCluster(
                    town=item["town"],
                    street_name=item["street_name"],
                    block=item["block"],
                    lease_commence_year=item["lease_commence_year"],
                    mop_completion_year=item["mop_completion_year"],
                    is_mop_upgrader_cohort=item["is_mop_upgrader_cohort"],
                    estimated_units=item["estimated_units"],
                    median_resale_psf=item["median_resale_psf"],
                )
                self.session.add(obj)
                existing_keys.add(key)
                count += 1

        await self.session.commit()
        return count

    async def sync_market_benchmarks(self, raw_records: list[dict[str, Any]]) -> int:
        """Clean, deduplicate, and upsert URA market price benchmarks."""
        cleaned_benchmarks = []
        for r in raw_records:
            bm = DataCleaner.clean_ura_benchmark_record(r)
            if bm:
                cleaned_benchmarks.append(bm)

        if not cleaned_benchmarks:
            return 0

        existing_res = await self.session.execute(
            select(
                MarketPriceBenchmark.district,
                MarketPriceBenchmark.market_segment,
                MarketPriceBenchmark.property_category,
                MarketPriceBenchmark.snapshot_date,
            )
        )
        existing_keys = set(existing_res.all())

        count = 0
        for item in cleaned_benchmarks:
            key = (item["district"], item["market_segment"], item["property_category"], item["snapshot_date"])
            if key not in existing_keys:
                obj = MarketPriceBenchmark(
                    district=item["district"],
                    town=item["town"],
                    market_segment=item["market_segment"],
                    property_category=item["property_category"],
                    snapshot_date=item["snapshot_date"],
                    median_psf=item["median_psf"],
                    p25_psf=item["p25_psf"],
                    p75_psf=item["p75_psf"],
                    median_quantum=item["median_quantum"],
                    quarterly_volume=item["quarterly_volume"],
                )
                self.session.add(obj)
                existing_keys.add(key)
                count += 1

        await self.session.commit()
        return count

