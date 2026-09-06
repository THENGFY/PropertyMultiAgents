from typing import Any


class WhitespaceRecommendationBuilder:
    """Constructs strategic campaign angles and persona targeting based on whitespace characteristics."""

    PERSONAS = {
        "MOP_UPGRADER": "HDB 5-Year MOP Homeowners with Family / Primary School Children",
        "NEW_SALE_INVESTOR": "Affluent Upgraders & Single Professionals Seeking Capital Growth Near TEL/CRL",
        "WEALTH_PRESERVATION": "High-Net-Worth Landed & Core Central Region (CCR) Cash Buyers",
        "SCHOOL_FOCUSED": "Parents Targeting Phase 2C Primary 1 School Registration (within 1km)",
    }

    @classmethod
    def build_recommendation(
        cls,
        target_type: str,
        target_identifier: str,
        district: str,
        property_category: str,
        ad_competition_count: int,
        estimated_units: int,
    ) -> tuple[str, str]:
        """Returns (recommended_persona, recommended_hook_angle)."""
        if target_type == "MOP_PRECINCT":
            persona = cls.PERSONAS["MOP_UPGRADER"]
            hook = (
                f"🚨 Untapped {target_identifier} MOP Cluster ({estimated_units} Units, only {ad_competition_count} competing ads). "
                f"Launch campaign focused on: 'MOP Reached: How to Sell HDB at Peak PSF and Upgrade to an Executive Condominium with Full Grant'!"
            )
        elif "CCR" in target_identifier or district in ["D09", "D10", "D11"]:
            persona = cls.PERSONAS["WEALTH_PRESERVATION"]
            hook = (
                f"💎 Prime Luxury Whitespace in {district} ({target_identifier}). "
                f"Low competitor ad volume detected. Run high-ticket campaign highlighting: 'Freehold Asset Preservation & ABSD Exemption Restructuring'!"
            )
        elif property_category == "CONDO_APT" and target_type == "PROJECT":
            persona = cls.PERSONAS["NEW_SALE_INVESTOR"]
            hook = (
                f"📈 High-Demand New Launch Gap in {target_identifier} ({district}). "
                f"Competitors are absent. Target: 'Direct Developer Preview Slots & 1km Top School Priority Catchment'!"
            )
        else:
            persona = cls.PERSONAS["SCHOOL_FOCUSED"]
            hook = (
                f"🏫 Family District Opportunity in {target_identifier} ({district}). "
                f"Highlight: 'Verified 1km Catchment to Top Primary Schools with Instant Showflat Booking'!"
            )

        return persona, hook
