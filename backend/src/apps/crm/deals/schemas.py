"""Pydantic schemas for CRM deals."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class DealCreate(BaseModel):
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=200)
    contact_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    value: float = Field(0, ge=0)
    expected_close_date: date | None = None
    source: str | None = Field(None, max_length=50)
    notes: str | None = None

class DealUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    stage_id: uuid.UUID | None = None
    value: float | None = Field(None, ge=0)
    probability: int | None = Field(None, ge=0, le=100)
    expected_close_date: date | None = None
    notes: str | None = None
    status: Literal["open", "won", "lost"] | None = None
    lost_reason: str | None = Field(None, max_length=200)

class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    contact_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    title: str
    value: float
    currency: str
    probability: int
    expected_close_date: date | None = None
    assigned_to: uuid.UUID | None = None
    source: str | None = None
    notes: str | None = None
    status: str
    won_date: date | None = None
    lost_date: date | None = None
    lost_reason: str | None = None
    created_at: datetime
    updated_at: datetime

class StageHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    deal_id: uuid.UUID
    from_stage_id: uuid.UUID | None = None
    to_stage_id: uuid.UUID
    moved_by: uuid.UUID | None = None
    moved_at: datetime
