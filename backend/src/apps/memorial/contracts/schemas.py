"""Schemas Pydantic para contratos exequiales + beneficiarios."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


AffiliateType = Literal["individual", "familiar", "empresarial"]
PaymentFrequency = Literal["monthly", "quarterly", "semiannual", "annual"]
ContractStatus = Literal["active", "suspended", "cancelled", "expired"]


# ---------------------------------------------------------------- Beneficiary


class BeneficiaryBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    birth_date: date | None = None
    gender: str | None = Field(None, max_length=10)
    relationship: str | None = Field(None, max_length=50)
    is_titular: bool = False
    joined_at: date | None = None


class BeneficiaryCreate(BeneficiaryBase):
    pass


class BeneficiaryUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    relationship: str | None = None
    is_titular: bool | None = None
    removed_at: date | None = None
    removed_reason: str | None = None


class BeneficiaryResponse(BeneficiaryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    joined_at: date
    removed_at: date | None = None
    removed_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Contract


class ContractBase(BaseModel):
    plan_id: uuid.UUID
    affiliate_type: AffiliateType

    titular_first_name: str | None = Field(None, max_length=100)
    titular_last_name: str | None = Field(None, max_length=100)
    titular_business_name: str | None = Field(None, max_length=255)
    titular_document_type: str | None = Field(None, max_length=10)
    titular_document_number: str | None = Field(None, max_length=50)
    titular_email: EmailStr | None = None
    titular_phone: str | None = Field(None, max_length=50)
    titular_mobile: str | None = Field(None, max_length=50)
    titular_address: str | None = Field(None, max_length=255)

    payment_frequency: PaymentFrequency
    start_date: date
    notes: str | None = None


class ContractCreate(ContractBase):
    """Crea contrato + (opcional) beneficiarios en mismo request.
    El `fee_amount` se autocalcula desde plan + payment_frequency.
    """

    beneficiaries: list[BeneficiaryCreate] = []


class ContractUpdate(BaseModel):
    titular_first_name: str | None = None
    titular_last_name: str | None = None
    titular_business_name: str | None = None
    titular_document_type: str | None = None
    titular_document_number: str | None = None
    titular_email: EmailStr | None = None
    titular_phone: str | None = None
    titular_mobile: str | None = None
    titular_address: str | None = None
    payment_frequency: PaymentFrequency | None = None
    fee_amount: Decimal | None = Field(None, ge=0)
    next_payment_date: date | None = None
    notes: str | None = None


class ContractListItem(BaseModel):
    """Fila compacta del listado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    consecutive: int
    plan_id: uuid.UUID
    plan_name: str
    affiliate_type: str
    titular_display: str
    titular_document_number: str | None
    payment_frequency: str
    fee_amount: Decimal
    start_date: date
    next_payment_date: date | None
    status: str
    beneficiaries_count: int


class ContractResponse(ContractBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    plan_name: str | None = None
    plan_type: str | None = None
    fee_amount: Decimal
    next_payment_date: date | None
    status: str
    suspended_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    user_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    beneficiaries: list[BeneficiaryResponse] = []


class TransitionRequest(BaseModel):
    new_status: ContractStatus
    reason: str | None = None


class CoverageLookupResult(BaseModel):
    """Resultado del lookup por documento: contratos activos que cubren
    a una persona con ese documento (sea como titular o beneficiario)."""

    contract_id: uuid.UUID
    contract_code: str
    plan_name: str
    plan_type: str
    titular_display: str
    beneficiary_id: uuid.UUID
    beneficiary_name: str
    beneficiary_relationship: str | None
    is_titular: bool
    coverage_amount: Decimal
    status: str
