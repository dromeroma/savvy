"""Pydantic schemas for condo maintenance."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class MaintenanceCreate(BaseModel):
    property_id: uuid.UUID; unit_id: uuid.UUID | None = None
    title: str = Field(..., max_length=200); description: str | None = None
    category: Literal["plumbing", "electrical", "structural", "elevator", "cleaning", "security", "general", "other"] = "general"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"

class MaintenanceUpdate(BaseModel):
    assigned_to: str | None = Field(None, max_length=200)
    status: Literal["open", "in_progress", "completed", "cancelled"] | None = None
    estimated_cost: float | None = Field(None, ge=0)
    actual_cost: float | None = Field(None, ge=0)
    resolution: str | None = None

class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; property_id: uuid.UUID; unit_id: uuid.UUID | None = None
    title: str; description: str | None = None; category: str; priority: str
    assigned_to: str | None = None; estimated_cost: float | None = None; actual_cost: float | None = None
    status: str; resolution: str | None = None; created_at: datetime
