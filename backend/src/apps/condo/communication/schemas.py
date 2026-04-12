"""Pydantic schemas for condo announcements."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class AnnouncementCreate(BaseModel):
    property_id: uuid.UUID; title: str = Field(..., max_length=200); body: str | None = None
    category: Literal["general", "maintenance", "financial", "event", "security", "emergency"] = "general"
    priority: Literal["low", "normal", "high", "urgent"] = "normal"

class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; property_id: uuid.UUID; title: str; body: str | None = None
    category: str; priority: str; status: str; created_at: datetime
