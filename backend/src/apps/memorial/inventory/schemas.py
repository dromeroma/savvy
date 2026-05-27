"""Schemas Pydantic para inventario."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ItemCategory = Literal["casket", "urn", "flowers", "supplies", "vehicle_supplies", "other"]
MovementType = Literal["entry", "exit", "adjustment", "transfer_out", "transfer_in"]


class ItemBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=200)
    category: ItemCategory
    description: str | None = None
    unit: str = Field(default="unidad", max_length=20)
    min_stock: Decimal = Field(default=Decimal("0"), ge=0)
    max_stock: Decimal | None = Field(None, ge=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    sale_price: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True
    notes: str | None = None


class ItemCreate(ItemBase):
    """Stock inicial opcional al crear. Si se pasa, se registra como
    movimiento de entrada con motivo 'stock_inicial'."""

    initial_stock: Decimal = Field(default=Decimal("0"), ge=0)


class ItemUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    unit: str | None = None
    min_stock: Decimal | None = Field(None, ge=0)
    max_stock: Decimal | None = Field(None, ge=0)
    unit_cost: Decimal | None = Field(None, ge=0)
    sale_price: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    notes: str | None = None


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    current_stock: Decimal
    created_at: datetime
    updated_at: datetime


class ItemListItem(BaseModel):
    """Card compacta del catálogo, con flag de stock bajo."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    category: str
    unit: str
    current_stock: Decimal
    min_stock: Decimal
    max_stock: Decimal | None
    unit_cost: Decimal
    sale_price: Decimal
    is_active: bool
    is_low_stock: bool = False  # computed: current_stock <= min_stock


# ---------------------------------------------------------------- Movements


class MovementCreate(BaseModel):
    """Registrar movimiento. Tipo 'entry' SUMA stock; 'exit' RESTA;
    'adjustment' SETEA al valor absoluto (la qty viene firmada);
    transfer_out/in funcionan como exit/entry."""

    item_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal | None = Field(None, ge=0)
    reason: str | None = Field(None, max_length=80)
    reference_doc: str | None = Field(None, max_length=80)
    supplier: str | None = Field(None, max_length=150)
    service_id: uuid.UUID | None = None
    movement_date: date | None = None
    notes: str | None = None


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    item_id: uuid.UUID
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal | None
    reason: str | None
    reference_doc: str | None
    supplier: str | None
    service_id: uuid.UUID | None
    movement_date: date
    notes: str | None
    recorded_by: uuid.UUID | None
    created_at: datetime


class MovementListItem(BaseModel):
    """Fila enriquecida con nombre y código del item."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    consecutive: int
    item_id: uuid.UUID
    item_code: str
    item_name: str
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal | None
    reason: str | None
    movement_date: date
    created_at: datetime
