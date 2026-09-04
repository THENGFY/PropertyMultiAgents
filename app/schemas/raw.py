from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RawCEASalespersonPayload(BaseModel):
    """Strict schema contract for incoming data.gov.sg CEA Salesperson Register records."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    salesperson_name: str | None = Field(default=None, validation_alias="agent_name")
    registration_no: str | None = Field(default=None, validation_alias="cea_reg_no")
    estate_agent_name: str | None = Field(default=None, validation_alias="agency_name")
    estate_agent_licence_no: str | None = Field(default=None, validation_alias="agency_licence_no")
    telephone: str | None = Field(default=None, validation_alias="contact_number")
    status: str | None = "ACTIVE"
    registration_start_date: str | None = None
    registration_end_date: str | None = None

    @field_validator("salesperson_name", "registration_no", "estate_agent_name", "estate_agent_licence_no", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class RawCEATransactionPayload(BaseModel):
    """Strict schema contract for incoming data.gov.sg CEA Property Transaction records."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    salesperson_registration_no: str | None = Field(default=None, validation_alias="cea_reg_no")
    transaction_date: str | None = Field(default=None, validation_alias="transaction_date_month")
    type_of_transaction: str | None = Field(default=None, validation_alias="transaction_type")
    property_type: str | None = None
    district: str | None = None
    town: str | None = None
    transaction_ref: str | None = None

    @field_validator("salesperson_registration_no", "transaction_date", "type_of_transaction", "property_type", mode="before")
    @classmethod
    def sanitize_tx_strings(cls, v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None
