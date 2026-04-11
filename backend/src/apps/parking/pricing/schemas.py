"""Pydantic schemas for parking pricing."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class PricingRuleCreate(BaseModel):
    location_id: uuid.UUID | None = None
    name: str = Field(..., max_length=100)
    vehicle_type: str = Field("car", max_length=20)
    pricing_model: Literal["per_minute", "per_hour", "flat_rate", "daily", "dynamic"] = "per_minute"
    base_rate: float = Field(0, ge=0)
    min_charge: float = Field(0, ge=0)
    max_daily: float | None = Field(None, ge=0)
    grace_minutes: int = Field(15, ge=0)
    rules: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

class PricingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    location_id: uuid.UUID | None = None
    name: str
    vehicle_type: str
    pricing_model: str
    base_rate: float
    min_charge: float
    max_daily: float | None = None
    grace_minutes: int
    rules: dict[str, Any]
    is_default: bool
    status: str
    created_at: datetime

class SubscriptionCreate(BaseModel):
    name: str = Field(..., max_length=100)
    plan_type: Literal["monthly", "quarterly", "annual"] = "monthly"
    vehicle_type: str = Field("car", max_length=20)
    price: float = Field(..., gt=0)
    location_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    max_vehicles: int = Field(1, ge=1)

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    plan_type: str
    vehicle_type: str
    price: float
    location_id: uuid.UUID | None = None
    max_vehicles: int
    status: str
    created_at: datetime
