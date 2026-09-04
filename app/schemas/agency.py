from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgencyBase(BaseModel):
    licence_no: str
    agency_name: str


class AgencyCreate(AgencyBase):
    pass


class AgencyOut(AgencyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
