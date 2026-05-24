"""Pydantic schemas for water tariffs."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SubscriberType = Literal["residential", "commercial", "industrial", "official"]


class TariffBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    subscriber_type: SubscriberType = "residential"
    stratum: int | None = Field(None, ge=1, le=6)
    fixed_charge: Decimal = Field(default=Decimal("0"), ge=0)
    price_per_cubic: Decimal = Field(default=Decimal("0"), ge=0)
    basic_limit_cubic: Decimal | None = Field(None, ge=0)
    surplus_price_per_cubic: Decimal | None = Field(None, ge=0)
    reconnection_fee: Decimal = Field(default=Decimal("0"), ge=0)
    suspension_fee: Decimal = Field(default=Decimal("0"), ge=0)
    late_interest_rate: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True
    valid_from: date
    valid_to: date | None = None


class TariffCreate(TariffBase):
    pass


class TariffUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    subscriber_type: SubscriberType | None = None
    stratum: int | None = Field(None, ge=1, le=6)
    fixed_charge: Decimal | None = Field(None, ge=0)
    price_per_cubic: Decimal | None = Field(None, ge=0)
    basic_limit_cubic: Decimal | None = Field(None, ge=0)
    surplus_price_per_cubic: Decimal | None = Field(None, ge=0)
    reconnection_fee: Decimal | None = Field(None, ge=0)
    suspension_fee: Decimal | None = Field(None, ge=0)
    late_interest_rate: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class TariffResponse(TariffBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
