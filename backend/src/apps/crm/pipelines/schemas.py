"""Pydantic schemas for CRM pipelines."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class StageCreate(BaseModel):
    name: str = Field(..., max_length=100)
    sort_order: int = 0
    probability: int = Field(0, ge=0, le=100)
    color: str | None = Field(None, max_length=10)
    is_won: bool = False
    is_lost: bool = False

class StageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    sort_order: int
    probability: int
    color: str | None = None
    is_won: bool
    is_lost: bool
    rules: dict[str, Any]

class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    is_default: bool = False
    deal_rot_days: int = Field(30, ge=1)
    currency: str = Field("COP", max_length=3)
    stages: list[StageCreate] = Field(default_factory=list)

class PipelineUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    deal_rot_days: int | None = Field(None, ge=1)
    status: str | None = None

class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    is_default: bool
    deal_rot_days: int
    currency: str
    status: str
    stages: list[StageResponse] = Field(default_factory=list)
    created_at: datetime
