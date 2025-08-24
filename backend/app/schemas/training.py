from datetime import date, datetime
from pydantic import BaseModel


class TrainingBase(BaseModel):
    title: str
    assignee: str
    assigned_date: date
    completed_date: date | None = None
    status: str = "assigned"


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    title: str | None = None
    assignee: str | None = None
    assigned_date: date | None = None
    completed_date: date | None = None
    status: str | None = None


class TrainingRead(TrainingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True