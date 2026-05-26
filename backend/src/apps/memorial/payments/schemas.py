"""Schemas Pydantic para pagos de SavvyMemorial."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PaymentMethod = Literal["cash", "transfer", "card", "check", "online"]


class PaymentAllocationInput(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)


class PaymentCreate(BaseModel):
    """Registrar un pago. Si no se pasan allocations, se aplica FIFO a las
    facturas pendientes del titular (contrato) o de la familia (servicio)."""

    contract_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None
    payer_name: str = Field(..., min_length=1, max_length=255)
    payer_document: str | None = Field(None, max_length=50)
    payer_email: str | None = Field(None, max_length=255)
    payer_phone: str | None = Field(None, max_length=50)
    payment_date: date
    amount: Decimal = Field(..., gt=0)
    method: PaymentMethod = "cash"
    receipt_number: str | None = Field(None, max_length=40)
    reference: str | None = Field(None, max_length=100)
    notes: str | None = None
    allocations: list[PaymentAllocationInput] = []


class PaymentAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: uuid.UUID
    invoice_code: str
    amount: Decimal


class PaymentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    consecutive: int
    payment_date: date
    amount: Decimal
    method: str
    receipt_number: str | None
    payer_name: str
    contract_id: uuid.UUID | None
    service_id: uuid.UUID | None
    invoices_count: int = 0


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    contract_id: uuid.UUID | None
    service_id: uuid.UUID | None
    payer_name: str
    payer_document: str | None
    payer_email: str | None
    payer_phone: str | None
    payment_date: date
    amount: Decimal
    method: str
    receipt_number: str | None
    reference: str | None
    notes: str | None
    recorded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    allocations: list[PaymentAllocationResponse] = []
