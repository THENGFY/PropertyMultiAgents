import re
from typing import Any


class AdCreativeParser:
    """Deterministic regex & NLP hook extractor for property ad creatives."""

    HOOK_PATTERNS = {
        "UPGRADER_MOP": [
            r"5[\s-]?year[s]?\s+mop",
            r"mop\s+flat",
            r"upgrade\s+to\s+(?:condo|ec|executive)",
            r"hdb\s+to\s+(?:condo|ec)",
            r"asset\s+progression",
            r"mop\s+reached",
        ],
        "TOP_SCHOOL": [
            r"within\s+1\s?km",
            r"within\s+2\s?km",
            r"primary\s+school",
            r"phase\s+2c",
            r"pri\s+sch",
            r"chij|acs|taonan|nanyang|raffles|henry park|catholic high",
        ],
        "MRT_TRANSPORT": [
            r"\d+\s*mins?\s+walk\s+to\s+mrt",
            r"doorstep\s+mrt",
            r"sheltered\s+walkway",
            r"connected\s+to\s+mrt",
            r"interchange\s+station",
        ],
        "DEVELOPER_DISCOUNT": [
            r"developer\s+discount",
            r"direct\s+developer",
            r"early\s+bird",
            r"vvip\s+preview",
            r"star\s+buy",
            r"developer\s+sales\s+team",
            r"special\s+developer\s+promo",
        ],

        "FREE_VALUATION": [
            r"free\s+home\s+valuation",
            r"free\s+property\s+report",
            r"free\s+asset\s+progression\s+plan",
            r"x-value",
            r"know\s+your\s+home\s+worth",
        ],
        "ABSD_DECOUPLING": [
            r"decoupling",
            r"99-1\s+rule",
            r"absd\s+remission",
            r"buy\s+2nd\s+property\s+without\s+absd",
            r"avoid\s+absd",
        ],
    }

    @classmethod
    def detect_hooks(cls, text: str) -> list[str]:
        """Detect marketing hooks present in ad headline or body."""
        if not text:
            return []
        lowered = text.lower()
        matched_hooks = []
        for hook_name, patterns in cls.HOOK_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lowered, re.IGNORECASE):
                    matched_hooks.append(hook_name)
                    break
        return matched_hooks

    @classmethod
    def parse_ad_record(cls, raw: dict[str, Any], agent_id: str) -> dict[str, Any]:
        """Normalize raw ad creative into standardized schema dict."""
        headline = (raw.get("ad_headline") or raw.get("headline") or "").strip()
        body = (raw.get("ad_body") or raw.get("body") or "").strip()
        media_type = (raw.get("media_type") or "IMAGE").strip().upper()
        
        # Check for optional image OCR text or captions
        ocr_text = (raw.get("image_ocr_text") or raw.get("caption") or "").strip()
        full_text = f"{headline} {body} {ocr_text}".strip()

        detected = cls.detect_hooks(full_text)
        
        # OCR Fallback for text-free visual creatives
        if not detected and media_type in ["IMAGE", "CAROUSEL"] and (not headline or not body):
            detected = ["REQUIRES_IMAGE_OCR"]

        target_district = (raw.get("target_district") or "ALL").strip().upper()
        target_segment = (raw.get("target_segment") or "RESALE").strip().upper()
        cta = (raw.get("cta_type") or "LEARN_MORE").strip().upper()

        return {
            "agent_id": agent_id,
            "ad_archive_id": str(raw.get("ad_archive_id") or raw.get("id") or f"AD-{hash(full_text or str(raw)) % 10000000}"),
            "page_name": (raw.get("page_name") or "Real Estate Consultant").strip(),
            "ad_headline": headline[:500],
            "ad_body": body,
            "cta_type": cta,
            "media_type": media_type,
            "target_segment": target_segment,
            "target_district": target_district,
            "start_date": raw.get("start_date"),
            "is_active": bool(raw.get("is_active", True)),
            "detected_hooks": detected,
        }

