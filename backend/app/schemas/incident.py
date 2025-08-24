from datetime import date, datetime
from pydantic import BaseModel


class IncidentBase(BaseModel):
    title: str
    description: str
    incident_date: date
    status: str = "open"


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    incident_date: date | None = None
    status: str | None = None


class IncidentRead(IncidentBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True