"""Schemas Pydantic para facturas de SavvyMemorial."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SourceType = Literal["exequial_dues", "service"]
InvoiceStatus = Literal["pending", "partial", "paid", "overdue", "annulled"]


class InvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    consecutive: int
    source_type: str
    contract_id: uuid.UUID | None
    service_id: uuid.UUID | None
    responsible_name: str
    issue_date: date
    due_date: date
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str
    description: str | None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    source_type: str
    contract_id: uuid.UUID | None
    service_id: uuid.UUID | None
    responsible_name: str
    responsible_document: str | None
    responsible_email: str | None
    responsible_phone: str | None
    responsible_address: str | None
    period_start: date | None
    period_end: date | None
    issue_date: date
    due_date: date
    subtotal: Decimal
    late_interest: Decimal
    surcharges: Decimal
    discounts: Decimal
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str
    description: str | None
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class BatchGenerateRequest(BaseModel):
    """Genera cuotas exequiales para todos los contratos con next_payment_date
    <= as_of_date. Si se omite, usa hoy."""

    as_of_date: date | None = None


class BatchGenerateResult(BaseModel):
    generated: int
    skipped_no_fee: int = 0
    invoice_ids: list[uuid.UUID] = []


class GenerateServiceInvoiceRequest(BaseModel):
    """Crea la factura única del servicio funerario a partir de final_total."""

    service_id: uuid.UUID
    due_days: int = Field(default=15, ge=0, le=365)
    surcharges: Decimal = Field(default=Decimal("0"), ge=0)
    discounts: Decimal = Field(default=Decimal("0"), ge=0)
    description: str | None = None
    notes: str | None = None
