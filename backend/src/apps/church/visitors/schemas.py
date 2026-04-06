"""Pydantic schemas for church visitors."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VisitorCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=50)
    email: str | None = None
    visit_date: date
    how_found: str | None = Field(None, max_length=100)
    notes: str | None = None


class VisitorUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    email: str | None = None
    how_found: str | None = Field(None, max_length=100)
    notes: str | None = None
    status: Literal["new", "contacted", "follow_up", "converted", "not_interested"] | None = None


class VisitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None
    visit_date: date
    how_found: str | None = None
    notes: str | None = None
    status: str
    converted_person_id: uuid.UUID | None = None
    created_at: datetime
