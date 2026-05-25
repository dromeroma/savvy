"""Pydantic schemas for the customer portal."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PortalMe(BaseModel):
    """Subscriber profile + org context for the portal header."""

    model_config = ConfigDict(from_attributes=True)

    subscriber_id: uuid.UUID
    code: str
    name: str
    email: str | None
    phone: str | None
    mobile: str | None
    address: str | None
    neighborhood: str | None
    stratum: int | None
    subscriber_type: str
    status: str
    organization_id: uuid.UUID
    organization_name: str


class PortalDashboard(BaseModel):
    open_balance: Decimal
    overdue_count: int
    pending_count: int
    last_invoice_date: date | None
    last_payment_date: date | None
    last_consumption_cubic: Decimal | None
    last_consumption_period: str | None  # "YYYY-MM"


class PortalInvoiceItem(BaseModel):
    id: uuid.UUID
    consecutive: int
    period_year: int
    period_month: int
    issue_date: date
    due_date: date
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str
    consumption_cubic: Decimal


class PortalPaymentItem(BaseModel):
    id: uuid.UUID
    payment_date: date
    amount: Decimal
    method: str
    receipt_number: str | None
    invoices_count: int


class PortalConsumptionItem(BaseModel):
    period_year: int
    period_month: int
    reading_date: date
    previous_reading: Decimal
    current_reading: Decimal
    consumption_cubic: Decimal


class PortalPqrsListItem(BaseModel):
    id: uuid.UUID
    code: str
    type: str
    subject: str
    status: str
    created_at: datetime
    responded_at: datetime | None


class PortalPqrsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    type: str
    subject: str
    description: str
    status: str
    response: str | None
    created_at: datetime
    responded_at: datetime | None
