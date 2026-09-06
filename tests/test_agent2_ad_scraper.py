import pytest
from app.agents.agent2_ad_scraper.ad_parser import AdCreativeParser
from app.agents.agent2_ad_scraper.meta_ad_client import MetaAdLibraryClient


def test_ad_creative_hook_detection():
    # 1. Test MOP hook
    text_mop = "5-Year MOP flat reached in Punggol! Upgrade to an Executive Condominium with grant entitlement."
    hooks_mop = AdCreativeParser.detect_hooks(text_mop)
    assert "UPGRADER_MOP" in hooks_mop

    # 2. Test Top School hook
    text_school = "Rare luxury condo within 1km to Nanyang Primary and ACS Junior."
    hooks_school = AdCreativeParser.detect_hooks(text_school)
    assert "TOP_SCHOOL" in hooks_school

    # 3. Test Developer Discount & ABSD Decoupling
    text_multi = "Direct developer discount preview! Learn how to buy a 2nd property with decoupling and avoid ABSD."
    hooks_multi = AdCreativeParser.detect_hooks(text_multi)
    assert "DEVELOPER_DISCOUNT" in hooks_multi
    assert "ABSD_DECOUPLING" in hooks_multi


def test_ad_parser_normalization():
    raw = {
        "ad_headline": "Direct Developer Price at Norwood Grand",
        "ad_body": "Walk 3 mins to MRT. Within 1km to top school.",
        "cta_type": "BOOK_NOW",
        "target_district": "d25",
        "media_type": "video",
        "is_active": True,
    }
    parsed = AdCreativeParser.parse_ad_record(raw=raw, agent_id="agent-uuid-123")
    assert parsed["agent_id"] == "agent-uuid-123"
    assert parsed["target_district"] == "D25"
    assert parsed["media_type"] == "VIDEO"
    assert "DEVELOPER_DISCOUNT" in parsed["detected_hooks"]
    assert "TOP_SCHOOL" in parsed["detected_hooks"]


@pytest.mark.asyncio
async def test_meta_ad_client_generation():
    client = MetaAdLibraryClient()
    ads = await client.fetch_active_ads_for_agent(
        agent_name="Tan Rachel", cea_reg_no="R0331148Q", limit=3
    )
    assert len(ads) >= 1
    assert "ad_headline" in ads[0]
    assert "target_segment" in ads[0]
    assert ads[0]["is_active"] is True


def test_ad_creative_image_ocr_fallback():
    # Ad with empty headline and body but media_type IMAGE
    raw_image_ad = {
        "ad_headline": "",
        "ad_body": "",
        "media_type": "IMAGE",
        "target_district": "D10",
        "is_active": True,
    }
    parsed = AdCreativeParser.parse_ad_record(raw=raw_image_ad, agent_id="agent-ocr-1")
    assert parsed["detected_hooks"] == ["REQUIRES_IMAGE_OCR"]

    # Ad with image caption supplied via OCR
    raw_with_ocr = {
        "ad_headline": "",
        "ad_body": "",
        "image_ocr_text": "5-Year MOP flat reached in Punggol!",
        "media_type": "IMAGE",
        "target_district": "D19",
        "is_active": True,
    }
    parsed_ocr = AdCreativeParser.parse_ad_record(raw=raw_with_ocr, agent_id="agent-ocr-2")
    assert "UPGRADER_MOP" in parsed_ocr["detected_hooks"]

