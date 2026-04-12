"""Pydantic schemas for POS inventory."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class InventoryAdjustment(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    location_id: uuid.UUID
    quantity: float
    movement_type: Literal["purchase", "sale", "adjustment", "transfer_in", "transfer_out", "return"]
    unit_cost: float | None = None
    notes: str | None = None

class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; product_id: uuid.UUID; variant_id: uuid.UUID | None = None
    location_id: uuid.UUID; quantity: float; min_stock: float; max_stock: float | None = None

class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; product_id: uuid.UUID; variant_id: uuid.UUID | None = None
    location_id: uuid.UUID; movement_type: str; quantity: float
    unit_cost: float | None = None; reference_type: str | None = None
    reference_id: uuid.UUID | None = None; notes: str | None = None
    created_at: datetime
