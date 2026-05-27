"""Schemas para el portal del cliente (acceso público con JWT scope:portal)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PortalAuthRequest(BaseModel):
    org_slug: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    document_number: str | None = Field(None, min_length=1, max_length=50)


class PortalAuthResponse(BaseModel):
    token: str
    expires_in_seconds: int
    contract: "PortalContract"


# ---------- Portal data shapes (defensive, do not leak internal fields)


class PortalBeneficiary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_name: str
    last_name: str | None = None
    document_number: str | None = None
    relationship: str | None = None
    is_titular: bool
    joined_at: date


class PortalContract(BaseModel):
    id: uuid.UUID
    code: str
    plan_name: str
    plan_code: str
    affiliate_type: Literal["individual", "familiar", "empresarial"]
    titular_first_name: str | None = None
    titular_last_name: str | None = None
    titular_business_name: str | None = None
    titular_email: str | None = None
    titular_phone: str | None = None
    titular_mobile: str | None = None
    titular_address: str | None = None
    payment_frequency: Literal["monthly", "quarterly", "semiannual", "annual"]
    fee_amount: Decimal
    start_date: date
    next_payment_date: date | None = None
    status: Literal["active", "suspended", "cancelled", "expired"]
    beneficiaries: list[PortalBeneficiary] = []
    organization_name: str


class PortalInvoiceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    issue_date: date
    due_date: date
    subtotal: Decimal
    discounts: Decimal
    late_interest: Decimal
    surcharges: Decimal
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: Literal["pending", "partial", "paid", "overdue", "annulled"]
    source_type: Literal["exequial_dues", "service"]
    description: str | None = None


class PortalPaymentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    payment_date: date
    amount: Decimal
    method: Literal["cash", "transfer", "card", "check", "online"]
    reference: str | None = None
    notes: str | None = None


class PortalServiceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    deceased_first_name: str
    deceased_last_name: str | None = None
    deceased_death_date: date
    service_type: str
    status: str
    final_total: Decimal


PortalAuthResponse.model_rebuild()
