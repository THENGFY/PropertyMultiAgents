from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    transaction_ref: str
    transaction_date: date
    property_type: str
    property_category: str = "CONDO_APT"
    transaction_type: str
    district: str | None = None
    town: str | None = None


class TransactionCreate(TransactionBase):
    agent_id: str
    raw_payload: dict[str, Any] | None = None


class TransactionOut(TransactionBase):
    id: str
    agent_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
