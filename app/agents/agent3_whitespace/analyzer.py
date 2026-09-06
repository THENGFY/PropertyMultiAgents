from datetime import date, datetime, timezone
import logging
from typing import Any
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent3_whitespace.recommendation_builder import WhitespaceRecommendationBuilder
from app.models.ad_campaign import AdCampaign
from app.models.market_benchmark import MarketPriceBenchmark
from app.models.mop_cluster import HDBMOPCluster
from app.models.whitespace_opportunity import WhitespaceOpportunity

logger = logging.getLogger(__name__)


class WhitespaceAnalyzer:
    """Detects market whitespace by cross-correlating Agent 1 demand data with Agent 2 ad density at subzone granularity."""

    TOWN_DISTRICT_MAP = {
        "PUNGGOL": "D19",
        "SENGKANG": "D19",
        "HOUGANG": "D19",
        "SERANGOON": "D19",
        "TAMPINES": "D18",
        "PASIR_RIS": "D18",
        "BEDOK": "D16",
        "MARINE_PARADE": "D15",
        "BUKIT_TIMAH": "D10",
        "ORCHARD": "D09",
        "QUEENSTOWN": "D03",
        "ANG_MO_KIO": "D20",
        "BISHAN": "D20",
        "TOA_PAYOH": "D12",
        "WOODLANDS": "D25",
        "JURONG_EAST": "D22",
        "JURONG_WEST": "D22",
        "YISHUN": "D27",
        "SEMBAWANG": "D27",
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def compute_whitespace_opportunities(
        self, snapshot_date: date | None = None
    ) -> list[WhitespaceOpportunity]:
        """Calculates whitespace opportunity scores across subzones, HDB MOP clusters and private property benchmarks."""
        ref_date = snapshot_date or date.today()

        # 1. Fetch active ad campaigns
        active_ads_res = await self.session.execute(
            select(AdCampaign).where(AdCampaign.is_active == True)
        )
        active_ads = active_ads_res.scalars().all()

        ad_district_counts: dict[str, int] = {}
        for ad in active_ads:
            dist = ad.target_district.upper()
            ad_district_counts[dist] = ad_district_counts.get(dist, 0) + 1

        # 2. Fetch HDB MOP Upgrader Clusters from Agent 1
        mop_clusters_res = await self.session.execute(
            select(HDBMOPCluster).where(HDBMOPCluster.is_mop_upgrader_cohort == True)
        )
        mop_clusters = mop_clusters_res.scalars().all()

        # 3. Fetch Market Price Benchmarks from Agent 1
        benchmarks_res = await self.session.execute(
            select(MarketPriceBenchmark)
        )
        benchmarks = benchmarks_res.scalars().all()

        # Clear existing opportunities for this snapshot date
        await self.session.execute(
            delete(WhitespaceOpportunity).where(WhitespaceOpportunity.snapshot_date == ref_date)
        )

        opportunities: list[WhitespaceOpportunity] = []

        # --- A. Evaluate HDB MOP Subzone Precincts ---
        town_mop_map: dict[str, dict[str, Any]] = {}
        for mop in mop_clusters:
            t = mop.town.upper()
            if t not in town_mop_map:
                town_mop_map[t] = {"units": 0, "mop_year": mop.mop_completion_year, "psf": mop.median_resale_psf}
            town_mop_map[t]["units"] += mop.estimated_units

        for town, data in town_mop_map.items():
            assigned_district = self.TOWN_DISTRICT_MAP.get(town, "D19")
            demand_index = min(1.0, max(0.2, data["units"] / 1000.0))
            
            # Subzone-level competition resolution:
            # 1. Direct subzone / town name mentions in ad text (Headline + Body)
            # 2. General district ads that don't specify another town receive fractional weight
            clean_town_keyword = town.lower().replace("_", " ")
            direct_subzone_ads = 0
            generic_district_ads = 0

            for ad in active_ads:
                ad_text = f"{ad.ad_headline} {ad.ad_body}".lower()
                if clean_town_keyword in ad_text:
                    direct_subzone_ads += 1
                elif ad.target_district == assigned_district:
                    # Check if ad explicitly targeted a competing subzone in same district
                    has_other_subzone = False
                    for other_t in self.TOWN_DISTRICT_MAP:
                        if other_t != town and other_t.lower().replace("_", " ") in ad_text:
                            has_other_subzone = True
                            break
                    if not has_other_subzone:
                        generic_district_ads += 1

            # Effective subzone ad competition: full weight for direct mentions + 30% for generic district ads
            effective_comp = direct_subzone_ads + (generic_district_ads * 0.3)
            ad_comp_index = min(1.0, effective_comp / 8.0)

            score = round(demand_index * (1.0 - (0.8 * ad_comp_index)) * 100, 1)

            persona, hook = WhitespaceRecommendationBuilder.build_recommendation(
                target_type="MOP_PRECINCT",
                target_identifier=f"{town} MOP Cluster",
                district=assigned_district,
                property_category="HDB",
                ad_competition_count=direct_subzone_ads,
                estimated_units=data["units"],
            )

            opp = WhitespaceOpportunity(
                target_type="MOP_PRECINCT",
                target_identifier=f"{town} MOP Cluster",
                district=assigned_district,
                property_category="HDB",
                market_demand_index=round(demand_index, 2),
                ad_competition_index=round(ad_comp_index, 2),
                whitespace_score=score,
                recommended_persona=persona,
                recommended_hook_angle=hook,
                estimated_target_units=data["units"],
                snapshot_date=ref_date,
            )
            self.session.add(opp)
            opportunities.append(opp)

        # --- B. Evaluate Private Residential Subzones & Districts ---
        district_map: dict[str, dict[str, Any]] = {}
        for b in benchmarks:
            dist = b.district.upper()
            if dist not in district_map:
                district_map[dist] = {
                    "town": b.town.upper(),
                    "district": dist,
                    "property_category": b.property_category,
                    "quarterly_volume": 0,
                }
            district_map[dist]["quarterly_volume"] += b.quarterly_volume

        for dist, data in district_map.items():
            comp_ads = ad_district_counts.get(dist, 0)
            demand_index = min(1.0, max(0.3, data["quarterly_volume"] / 50.0))
            ad_comp_index = min(1.0, comp_ads / 12.0)
            score = round(demand_index * (1.0 - (0.8 * ad_comp_index)) * 100, 1)

            target_id = f"{data['town']} ({dist})"

            persona, hook = WhitespaceRecommendationBuilder.build_recommendation(
                target_type="DISTRICT",
                target_identifier=target_id,
                district=dist,
                property_category=data["property_category"],
                ad_competition_count=comp_ads,
                estimated_units=data["quarterly_volume"] * 10,
            )

            opp = WhitespaceOpportunity(
                target_type="DISTRICT",
                target_identifier=target_id,
                district=dist,
                property_category=data["property_category"],
                market_demand_index=round(demand_index, 2),
                ad_competition_index=round(ad_comp_index, 2),
                whitespace_score=score,
                recommended_persona=persona,
                recommended_hook_angle=hook,
                estimated_target_units=data["quarterly_volume"] * 10,
                snapshot_date=ref_date,
            )
            self.session.add(opp)
            opportunities.append(opp)

        await self.session.commit()
        return opportunities
