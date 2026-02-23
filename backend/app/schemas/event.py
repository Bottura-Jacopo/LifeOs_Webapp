from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=32)
    start_time: datetime
    end_time: datetime | None = None
    score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class EventOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    start_time: datetime
    end_time: datetime | None
    score: int | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class EventUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=32)
    start_time: datetime | None = None
    end_time: datetime | None = None
    score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None