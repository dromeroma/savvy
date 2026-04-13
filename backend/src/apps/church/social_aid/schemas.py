"""Pydantic schemas for social aid sub-module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# -----------------------------------------------------------------
# Programs
# -----------------------------------------------------------------

PROGRAM_TYPE = Literal[
    "food", "clothing", "medical", "educational", "housing", "emergency", "other",
]
PROGRAM_STATUS = Literal["active", "paused", "completed", "cancelled"]


class AidProgramCreate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    program_type: PROGRAM_TYPE = "food"
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = Field(None, ge=0)
    status: PROGRAM_STATUS = "active"


class AidProgramUpdate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    program_type: PROGRAM_TYPE | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = Field(None, ge=0)
    status: PROGRAM_STATUS | None = None


class AidProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str
    program_type: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------
# Beneficiaries
# -----------------------------------------------------------------

class BeneficiaryCreate(BaseModel):
    program_id: uuid.UUID
    person_id: uuid.UUID | None = None
    external_name: str | None = Field(None, max_length=200)
    external_document: str | None = Field(None, max_length=50)
    external_phone: str | None = Field(None, max_length=30)
    need_category: str | None = Field(None, max_length=60)
    household_size: int | None = Field(None, ge=1)
    notes: str | None = None

    @model_validator(mode="after")
    def require_identity(self) -> "BeneficiaryCreate":
        if self.person_id is None and not self.external_name:
            raise ValueError("Either person_id or external_name is required.")
        return self


class BeneficiaryUpdate(BaseModel):
    external_name: str | None = Field(None, max_length=200)
    external_document: str | None = Field(None, max_length=50)
    external_phone: str | None = Field(None, max_length=30)
    need_category: str | None = Field(None, max_length=60)
    household_size: int | None = Field(None, ge=1)
    notes: str | None = None
    status: str | None = None


class BeneficiaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    program_id: uuid.UUID
    person_id: uuid.UUID | None = None
    external_name: str | None = None
    external_document: str | None = None
    external_phone: str | None = None
    need_category: str | None = None
    household_size: int | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------
# Distributions
# -----------------------------------------------------------------

class DistributionCreate(BaseModel):
    program_id: uuid.UUID
    beneficiary_id: uuid.UUID
    distribution_date: date
    item_description: str = Field(..., min_length=1, max_length=300)
    quantity: Decimal | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=30)
    estimated_value: Decimal | None = Field(None, ge=0)
    delivered_by: uuid.UUID | None = None
    notes: str | None = None


class DistributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    program_id: uuid.UUID
    beneficiary_id: uuid.UUID
    distribution_date: date
    item_description: str
    quantity: Decimal | None = None
    unit: str | None = None
    estimated_value: Decimal | None = None
    delivered_by: uuid.UUID | None = None
    notes: str | None = None
    created_at: datetime
