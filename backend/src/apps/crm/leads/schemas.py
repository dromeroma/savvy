"""Pydantic schemas for CRM leads."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

LEAD_STATUS = Literal["new", "contacted", "qualified", "unqualified", "converted", "lost"]

class LeadCreate(BaseModel):
    contact_id: uuid.UUID
    source: str | None = Field(None, max_length=50)
    score: int = Field(0, ge=0)
    notes: str | None = None

class LeadUpdate(BaseModel):
    status: LEAD_STATUS | None = None
    score: int | None = Field(None, ge=0)
    assigned_to: uuid.UUID | None = None
    notes: str | None = None

class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    contact_id: uuid.UUID
    source: str | None = None
    score: int
    status: str
    assigned_to: uuid.UUID | None = None
    converted_deal_id: uuid.UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
