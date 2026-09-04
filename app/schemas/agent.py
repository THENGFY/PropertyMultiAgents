from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.agency import AgencyOut


class AgentBase(BaseModel):
    cea_reg_no: str
    agent_name: str
    contact_number: str | None = None
    status: str = "ACTIVE"
    registration_start_date: date | None = None
    registration_end_date: date | None = None


class AgentCreate(AgentBase):
    agency_id: str


class AgentOut(AgentBase):
    id: str
    agency_id: str
    agency: AgencyOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentSummary(BaseModel):
    id: str
    cea_reg_no: str
    agent_name: str
    agency_name: str
    agency_licence: str
    total_transactions_t12m: int
    new_sale_t12m: int
    resale_t12m: int
    rental_t12m: int
    overall_rank: int | None = None
    overall_percentile: float | None = None
