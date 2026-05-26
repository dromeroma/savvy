"""Schemas Pydantic para planes exequiales."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PlanType = Literal["individual", "familiar", "empresarial"]


class PlanBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    plan_type: PlanType
    max_beneficiaries: int | None = Field(None, ge=1)
    max_age_at_affiliation: int | None = Field(None, ge=0, le=120)
    max_age_for_coverage: int | None = Field(None, ge=0, le=120)
    waiting_period_days: int = Field(default=0, ge=0)

    monthly_fee: Decimal = Field(default=Decimal("0"), ge=0)
    quarterly_fee: Decimal = Field(default=Decimal("0"), ge=0)
    semiannual_fee: Decimal = Field(default=Decimal("0"), ge=0)
    annual_fee: Decimal = Field(default=Decimal("0"), ge=0)

    coverage_amount: Decimal = Field(default=Decimal("0"), ge=0)
    coverage_items: list[str] = []

    is_active: bool = True
    valid_from: date
    valid_to: date | None = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = None
    max_beneficiaries: int | None = Field(None, ge=1)
    max_age_at_affiliation: int | None = Field(None, ge=0, le=120)
    max_age_for_coverage: int | None = Field(None, ge=0, le=120)
    waiting_period_days: int | None = Field(None, ge=0)

    monthly_fee: Decimal | None = Field(None, ge=0)
    quarterly_fee: Decimal | None = Field(None, ge=0)
    semiannual_fee: Decimal | None = Field(None, ge=0)
    annual_fee: Decimal | None = Field(None, ge=0)

    coverage_amount: Decimal | None = Field(None, ge=0)
    coverage_items: list[str] | None = None

    is_active: bool | None = None
    valid_to: date | None = None


class PlanResponse(PlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PlanListItem(BaseModel):
    """Card compacto del catálogo."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    plan_type: str
    monthly_fee: Decimal
    coverage_amount: Decimal
    is_active: bool
    contracts_count: int = 0
