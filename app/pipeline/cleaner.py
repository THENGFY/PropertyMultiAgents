import re
from datetime import date, datetime
from typing import Any


class DataCleaner:
    """Sanitizes, validates, and normalizes raw CEA salesperson and transaction feeds."""

    # CEA Reg No: Starts with R or K, followed by 6-7 digits, ending with 1 letter
    CEA_REG_PATTERN = re.compile(r"^[RK]\d{6,7}[A-Z]$", re.IGNORECASE)
    # CEA Licence No: Starts with L, followed by 6-7 digits, ending with 1 letter
    CEA_LICENCE_PATTERN = re.compile(r"^L\d{6,7}[A-Z]$", re.IGNORECASE)

    SEGMENT_MAPPING = {
        "NEW SALE": "NEW_SALE",
        "NEW_SALE": "NEW_SALE",
        "DEVELOPER SALE": "NEW_SALE",
        "PRIMARY": "NEW_SALE",
        "RESALE": "RESALE",
        "SECONDARY": "RESALE",
        "SUB SALE": "RESALE",
        "RENTAL": "RENTAL",
        "LEASE": "RENTAL",
        "TENANCY": "RENTAL",
        "WHOLE RENTAL": "RENTAL",
        "ROOM RENTAL": "RENTAL",
    }

    PROPERTY_CATEGORY_MAPPING = {
        "HDB": "HDB",
        "4_ROOM": "HDB",
        "5_ROOM": "HDB",
        "3_ROOM": "HDB",
        "EXECUTIVE": "HDB",
        "TERRACE": "LANDED",
        "SEMI_DETACHED": "LANDED",
        "SEMI DETACHED": "LANDED",
        "GOOD_CLASS_BUNGALOW": "LANDED",
        "BUNGALOW": "LANDED",
        "DETACHED": "LANDED",
        "LANDED": "LANDED",
        "CONDO": "CONDO_APT",
        "APARTMENT": "CONDO_APT",
        "EXECUTIVE_CONDOMINIUM": "CONDO_APT",
        "COMMERCIAL": "COMMERCIAL",
        "OFFICE": "COMMERCIAL",
        "SHOPHOUSE": "COMMERCIAL",
        "RETAIL": "COMMERCIAL",
        "INDUSTRIAL": "COMMERCIAL",
    }

    @classmethod
    def normalize_property_category(cls, raw_prop: Any) -> str:
        """Categorize raw property type into HDB, CONDO_APT, LANDED, COMMERCIAL, or OTHER."""
        if not raw_prop or not isinstance(raw_prop, str):
            return "CONDO_APT"
        cleaned = raw_prop.strip().upper().replace(" ", "_")
        for key, category in cls.PROPERTY_CATEGORY_MAPPING.items():
            if key in cleaned:
                return category
        return "CONDO_APT"

    @classmethod
    def clean_cea_reg_no(cls, reg_no: Any) -> str | None:
        """Sanitize and validate CEA registration number."""
        if not reg_no or not isinstance(reg_no, str):
            return None
        cleaned = reg_no.strip().upper()
        if cls.CEA_REG_PATTERN.match(cleaned):
            return cleaned
        return None

    @classmethod
    def clean_licence_no(cls, licence_no: Any) -> str:
        """Sanitize and uppercase agency licence number."""
        if not licence_no or not isinstance(licence_no, str):
            return "L0000000Z"
        cleaned = licence_no.strip().upper()
        return cleaned

    @classmethod
    def clean_text(cls, text: Any, default: str = "") -> str:
        """Sanitize generic string fields."""
        if not text or not isinstance(text, str):
            return default
        return " ".join(text.strip().split())

    @classmethod
    def normalize_transaction_type(cls, raw_type: Any) -> str:
        """Map raw transaction type string to standard enum: NEW_SALE, RESALE, RENTAL."""
        if not raw_type or not isinstance(raw_type, str):
            return "RESALE"
        cleaned = raw_type.strip().upper().replace("-", " ")
        for key, val in cls.SEGMENT_MAPPING.items():
            if key in cleaned:
                return val
        return "RESALE"

    @classmethod
    def parse_date(cls, raw_date: Any) -> date | None:
        """Parse various date string formats into standard date object."""
        if not raw_date:
            return None
        if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
            return raw_date
        if isinstance(raw_date, datetime):
            return raw_date.date()

        cleaned_str = str(raw_date).strip()
        # Try multiple date formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y%m",  # e.g., 202405 (year-month)
            "%b-%Y",  # e.g., May-2024
            "%b %Y",  # e.g., May 2024
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned_str, fmt)
                return dt.date()
            except ValueError:
                continue

        # Handle YYYY-MM fallback
        if re.match(r"^\d{4}-\d{2}$", cleaned_str):
            try:
                return datetime.strptime(f"{cleaned_str}-01", "%Y-%m-%d").date()
            except ValueError:
                pass

        return None

    @classmethod
    def clean_agent_record(cls, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Validate and clean an agent dictionary."""
        reg_no = cls.clean_cea_reg_no(
            raw.get("cea_reg_no")
            or raw.get("salesperson_registration_no")
            or raw.get("registration_no")
            or raw.get("salesperson_reg_no")
        )
        if not reg_no:
            return None

        name = cls.clean_text(
            raw.get("agent_name")
            or raw.get("salesperson_name")
            or raw.get("name")
            or "Unknown Agent"
        )
        agency_licence = cls.clean_licence_no(
            raw.get("agency_licence_no")
            or raw.get("estate_agent_licence_no")
            or raw.get("licence_no")
        )
        agency_name = cls.clean_text(
            raw.get("agency_name")
            or raw.get("estate_agent_name")
            or "INDEPENDENT AGENCY"
        )
        contact = cls.clean_text(raw.get("contact_number") or raw.get("telephone"))

        return {
            "cea_reg_no": reg_no,
            "agent_name": name,
            "agency_licence_no": agency_licence,
            "agency_name": agency_name,
            "contact_number": contact or None,
            "status": raw.get("status", "ACTIVE").strip().upper(),
            "registration_start_date": cls.parse_date(raw.get("registration_start_date")),
            "registration_end_date": cls.parse_date(raw.get("registration_end_date")),
        }

    @classmethod
    def clean_transaction_record(cls, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Validate and clean a transaction dictionary."""
        reg_no = cls.clean_cea_reg_no(
            raw.get("cea_reg_no")
            or raw.get("salesperson_registration_no")
            or raw.get("salesperson_reg_no")
        )
        if not reg_no:
            return None

        tx_date = cls.parse_date(
            raw.get("transaction_date")
            or raw.get("transaction_date_month")
            or raw.get("date")
        )
        if not tx_date:
            return None

        tx_type = cls.normalize_transaction_type(
            raw.get("transaction_type")
            or raw.get("property_type_transaction")
            or raw.get("type_of_transaction")
            or raw.get("type")
        )

        ref = cls.clean_text(
            raw.get("transaction_ref")
            or raw.get("_id")
            or raw.get("id")
            or f"TX-{reg_no}-{tx_date.isoformat()}-{hash(str(raw)) % 1000000}"
        )

        prop_type = cls.clean_text(
            raw.get("property_type")
            or raw.get("property_category")
            or "RESIDENTIAL"
        )
        prop_category = cls.normalize_property_category(prop_type)
        district = cls.clean_text(raw.get("district")) or None
        town = cls.clean_text(raw.get("town")) or None

        return {
            "cea_reg_no": reg_no,
            "transaction_ref": ref,
            "transaction_date": tx_date,
            "property_type": prop_type,
            "property_category": prop_category,
            "transaction_type": tx_type,
            "district": district,
            "town": town,
            "raw_payload": raw,
        }

    @classmethod
    def clean_hdb_mop_record(cls, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Validate and clean an HDB MOP cluster record."""
        town = cls.clean_text(raw.get("town"))
        if not town:
            return None

        street = cls.clean_text(raw.get("street_name") or raw.get("street") or f"{town} ST")
        block = cls.clean_text(str(raw.get("block") or "101"))
        
        try:
            lease_year = int(raw.get("lease_commence_date") or raw.get("lease_commence_year") or 2018)
        except (ValueError, TypeError):
            lease_year = 2018

        mop_year = int(raw.get("mop_year") or (lease_year + 5))
        is_mop = bool(raw.get("is_mop_upgrader_cohort", False))
        
        try:
            units = int(raw.get("estimated_units_in_cluster") or raw.get("estimated_units") or 120)
        except (ValueError, TypeError):
            units = 120

        try:
            psf = float(raw.get("psf") or raw.get("median_resale_psf") or 550.0)
        except (ValueError, TypeError):
            psf = 550.0

        return {
            "town": town.upper(),
            "street_name": street.upper(),
            "block": block.upper(),
            "lease_commence_year": lease_year,
            "mop_completion_year": mop_year,
            "is_mop_upgrader_cohort": is_mop,
            "estimated_units": units,
            "median_resale_psf": round(psf, 2),
        }

    @classmethod
    def clean_ura_benchmark_record(cls, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Validate and clean a URA private residential market benchmark record."""
        district = cls.clean_text(raw.get("district") or "D10").upper()
        town = cls.clean_text(raw.get("town") or "CENTRAL").upper()
        market_segment = cls.clean_text(raw.get("market_segment") or "CCR").upper()
        prop_cat = cls.clean_text(raw.get("property_category") or "CONDO_APT").upper()
        
        snap_date = cls.parse_date(raw.get("snapshot_date") or raw.get("contract_date") or date.today())
        if not snap_date:
            snap_date = date.today()

        try:
            med_psf = float(raw.get("median_psf") or raw.get("unit_price_psf") or 2200.0)
        except (ValueError, TypeError):
            med_psf = 2200.0

        try:
            p25 = float(raw.get("p25_psf") or (med_psf * 0.9))
            p75 = float(raw.get("p75_psf") or (med_psf * 1.15))
            quantum = float(raw.get("median_quantum") or raw.get("transacted_price") or (med_psf * 950))
            vol = int(raw.get("quarterly_volume") or 25)
        except (ValueError, TypeError):
            p25 = med_psf * 0.9
            p75 = med_psf * 1.15
            quantum = med_psf * 950
            vol = 25

        return {
            "district": district,
            "town": town,
            "market_segment": market_segment,
            "property_category": prop_cat,
            "snapshot_date": snap_date,
            "median_psf": round(med_psf, 2),
            "p25_psf": round(p25, 2),
            "p75_psf": round(p75, 2),
            "median_quantum": round(quantum, 2),
            "quarterly_volume": vol,
        }

