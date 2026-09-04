from datetime import date
from app.pipeline.cleaner import DataCleaner


def test_clean_cea_reg_no_valid():
    assert DataCleaner.clean_cea_reg_no("R012345A") == "R012345A"
    assert DataCleaner.clean_cea_reg_no("  r098765z  ") == "R098765Z"
    assert DataCleaner.clean_cea_reg_no("K012345B") == "K012345B"


def test_clean_cea_reg_no_invalid():
    assert DataCleaner.clean_cea_reg_no("INVALID_REG") is None
    assert DataCleaner.clean_cea_reg_no("") is None
    assert DataCleaner.clean_cea_reg_no(None) is None
    assert DataCleaner.clean_cea_reg_no("R123") is None  # Too short
    assert DataCleaner.clean_cea_reg_no("A012345B") is None  # Doesn't start with R or K


def test_normalize_transaction_type():
    assert DataCleaner.normalize_transaction_type("New Sale") == "NEW_SALE"
    assert DataCleaner.normalize_transaction_type("DEVELOPER SALE") == "NEW_SALE"
    assert DataCleaner.normalize_transaction_type("Resale") == "RESALE"
    assert DataCleaner.normalize_transaction_type("SUB SALE") == "RESALE"
    assert DataCleaner.normalize_transaction_type("Whole Rental") == "RENTAL"
    assert DataCleaner.normalize_transaction_type("Room Rental") == "RENTAL"
    assert DataCleaner.normalize_transaction_type("Lease") == "RENTAL"
    assert DataCleaner.normalize_transaction_type("Unknown Type") == "RESALE"  # Default fallback


def test_parse_date_formats():
    assert DataCleaner.parse_date("2024-05-15") == date(2024, 5, 15)
    assert DataCleaner.parse_date("15/05/2024") == date(2024, 5, 15)
    assert DataCleaner.parse_date("2024-05") == date(2024, 5, 1)
    assert DataCleaner.parse_date("202405") == date(2024, 5, 1)
    assert DataCleaner.parse_date("May-2024") == date(2024, 5, 1)
    assert DataCleaner.parse_date(None) is None
    assert DataCleaner.parse_date("not-a-date") is None


def test_clean_agent_record_dirty_payload():
    dirty = {
        "salesperson_registration_no": "  r012345A ",
        "salesperson_name": "  Tan   Wei Ming  ",
        "estate_agent_licence_no": " l3008022j ",
        "estate_agent_name": "  PROPEXCELLENCE PTE LTD  ",
        "telephone": "  +65 91234567 ",
        "status": " active ",
        "registration_start_date": "2020-01-01",
    }
    cleaned = DataCleaner.clean_agent_record(dirty)
    assert cleaned is not None
    assert cleaned["cea_reg_no"] == "R012345A"
    assert cleaned["agent_name"] == "Tan Wei Ming"
    assert cleaned["agency_licence_no"] == "L3008022J"
    assert cleaned["agency_name"] == "PROPEXCELLENCE PTE LTD"
    assert cleaned["contact_number"] == "+65 91234567"
    assert cleaned["status"] == "ACTIVE"
    assert cleaned["registration_start_date"] == date(2020, 1, 1)


def test_clean_transaction_record():
    raw_tx = {
        "salesperson_registration_no": "R012345A",
        "transaction_date": "2024-06-15",
        "type_of_transaction": "DEVELOPER SALE",
        "property_type": "CONDOMINIUM_APARTMENTS",
        "district": "D09",
    }
    cleaned = DataCleaner.clean_transaction_record(raw_tx)
    assert cleaned is not None
    assert cleaned["cea_reg_no"] == "R012345A"
    assert cleaned["transaction_date"] == date(2024, 6, 15)
    assert cleaned["transaction_type"] == "NEW_SALE"
    assert cleaned["district"] == "D09"
