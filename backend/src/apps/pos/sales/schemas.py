"""Pydantic schemas for POS sales."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class SaleLineCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: float = Field(..., gt=0)
    unit_price: float | None = None  # Override price
    discount: float = Field(0, ge=0)

class SaleCreate(BaseModel):
    location_id: uuid.UUID
    register_id: uuid.UUID | None = None
    customer_person_id: uuid.UUID | None = None
    lines: list[SaleLineCreate] = Field(..., min_length=1)
    payment_method: Literal["cash", "card", "bank_transfer", "credit", "mixed"] = "cash"
    payment_details: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None

class SaleLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; sale_id: uuid.UUID; product_id: uuid.UUID; variant_id: uuid.UUID | None = None
    product_name: str; sku: str; quantity: float; unit_price: float
    discount: float; tax_rate: float; tax_amount: float; line_total: float

class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; sale_number: str
    location_id: uuid.UUID; register_id: uuid.UUID | None = None
    customer_person_id: uuid.UUID | None = None; cashier_id: uuid.UUID | None = None
    subtotal: float; discount_amount: float; tax_amount: float; total: float
    payment_method: str; pay_transaction_id: uuid.UUID | None = None
    status: str; notes: str | None = None
    lines: list[SaleLineResponse] = Field(default_factory=list)
    created_at: datetime
