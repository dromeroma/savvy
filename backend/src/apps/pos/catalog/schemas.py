"""Pydantic schemas for POS catalog."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class LocationCreate(BaseModel):
    code: str = Field(..., max_length=30); name: str = Field(..., max_length=200)
    address: str | None = None; city: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)

class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; code: str; name: str; address: str | None = None; city: str | None = None
    phone: str | None = None; status: str; created_at: datetime

class CategoryCreate(BaseModel):
    code: str = Field(..., max_length=30); name: str = Field(..., max_length=200)
    parent_id: uuid.UUID | None = None; sort_order: int = 0

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; code: str; name: str; parent_id: uuid.UUID | None = None
    sort_order: int; status: str

class VariantCreate(BaseModel):
    sku: str = Field(..., max_length=50); name: str = Field(..., max_length=200)
    attributes: dict[str, Any] = Field(default_factory=dict)
    price_override: float | None = Field(None, ge=0)
    cost_override: float | None = Field(None, ge=0)
    barcode: str | None = Field(None, max_length=50)

class VariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; product_id: uuid.UUID; sku: str; name: str
    attributes: dict[str, Any]; price_override: float | None = None
    cost_override: float | None = None; barcode: str | None = None

class ProductCreate(BaseModel):
    category_id: uuid.UUID | None = None
    sku: str = Field(..., max_length=50); name: str = Field(..., max_length=200)
    barcode: str | None = Field(None, max_length=50)
    description: str | None = None
    product_type: Literal["simple", "variant", "bundle", "service", "recipe"] = "simple"
    price: float = Field(0, ge=0); cost: float = Field(0, ge=0)
    tax_id: uuid.UUID | None = None
    tracks_inventory: bool = True
    image_url: str | None = Field(None, max_length=500)
    variants: list[VariantCreate] = Field(default_factory=list)

class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    price: float | None = Field(None, ge=0)
    cost: float | None = Field(None, ge=0)
    category_id: uuid.UUID | None = None
    tracks_inventory: bool | None = None
    status: Literal["active", "inactive"] | None = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; category_id: uuid.UUID | None = None
    sku: str; barcode: str | None = None; name: str; description: str | None = None
    product_type: str; price: float; cost: float; tax_id: uuid.UUID | None = None
    tracks_inventory: bool; image_url: str | None = None; status: str
    variants: list[VariantResponse] = Field(default_factory=list)
    created_at: datetime
