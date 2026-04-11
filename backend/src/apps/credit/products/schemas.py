"""Pydantic v2 schemas for SavvyCredit products."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

INTEREST_TYPE = Literal["fixed", "declining_balance", "flat", "compound"]
AMORT_METHOD = Literal["french", "german", "flat", "bullet"]
FREQUENCY = Literal["weekly", "biweekly", "monthly", "quarterly", "custom"]
FEE_TYPE = Literal["percentage", "fixed", "none"]
ALLOCATION = Literal["interest_first", "principal_first", "proportional"]
RATE_PERIOD = Literal["monthly", "annual", "daily"]


class ProductFeeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    fee_type: Literal["percentage", "fixed"] = "fixed"
    value: float = Field(..., ge=0)
    applies_to: Literal["disbursement", "monthly", "annual"] = "disbursement"
    is_required: bool = True


class ProductFeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    fee_type: str
    value: float
    applies_to: str
    is_required: bool


class CreditProductCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    interest_type: INTEREST_TYPE = "declining_balance"
    interest_rate: float = Field(0, ge=0)
    interest_rate_period: RATE_PERIOD = "monthly"
    amortization_method: AMORT_METHOD = "french"
    payment_frequency: FREQUENCY = "monthly"
    term_min: int = Field(1, ge=1)
    term_max: int = Field(60, ge=1)
    amount_min: float = Field(0, ge=0)
    amount_max: float = Field(999999999, ge=0)
    grace_period_days: int = Field(0, ge=0)
    late_fee_type: FEE_TYPE = "none"
    late_fee_value: float = Field(0, ge=0)
    payment_allocation: ALLOCATION = "interest_first"
    origination_fee_type: FEE_TYPE = "none"
    origination_fee_value: float = Field(0, ge=0)
    requires_guarantor: bool = False
    max_guarantors: int = Field(1, ge=0)
    settings: dict[str, Any] = Field(default_factory=dict)
    fees: list[ProductFeeCreate] = Field(default_factory=list)


class CreditProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    interest_rate: float | None = Field(None, ge=0)
    term_min: int | None = Field(None, ge=1)
    term_max: int | None = Field(None, ge=1)
    amount_min: float | None = Field(None, ge=0)
    amount_max: float | None = Field(None, ge=0)
    grace_period_days: int | None = Field(None, ge=0)
    late_fee_type: FEE_TYPE | None = None
    late_fee_value: float | None = Field(None, ge=0)
    origination_fee_type: FEE_TYPE | None = None
    origination_fee_value: float | None = Field(None, ge=0)
    requires_guarantor: bool | None = None
    settings: dict[str, Any] | None = None
    status: Literal["active", "inactive", "archived"] | None = None


class CreditProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    interest_type: str
    interest_rate: float
    interest_rate_period: str
    amortization_method: str
    payment_frequency: str
    term_min: int
    term_max: int
    amount_min: float
    amount_max: float
    grace_period_days: int
    late_fee_type: str
    late_fee_value: float
    payment_allocation: str
    origination_fee_type: str
    origination_fee_value: float
    requires_guarantor: bool
    max_guarantors: int
    settings: dict[str, Any]
    status: str
    fees: list[ProductFeeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
