"""Pydantic v2 schemas for SavvyCredit loans."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoanCreate(BaseModel):
    """Create a loan from an approved application or directly."""
    borrower_id: uuid.UUID
    product_id: uuid.UUID
    application_id: uuid.UUID | None = None
    principal: float = Field(..., gt=0)
    term: int = Field(..., ge=1)
    interest_rate_override: float | None = Field(None, ge=0)
    disbursement_date: date | None = None
    first_payment_date: date | None = None
    notes: str | None = None


class DisburseLoan(BaseModel):
    method: Literal["cash", "bank_transfer", "check", "mobile_payment"] = "cash"
    disbursement_date: date | None = None
    notes: str | None = None


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    borrower_id: uuid.UUID
    product_id: uuid.UUID
    application_id: uuid.UUID | None = None
    loan_number: str
    principal: float
    interest_rate: float
    interest_type: str
    amortization_method: str
    payment_frequency: str
    total_installments: int
    payment_allocation: str
    disbursement_date: date | None = None
    first_payment_date: date | None = None
    maturity_date: date | None = None
    next_payment_date: date | None = None
    balance_principal: float
    balance_interest: float
    balance_penalties: float
    total_paid: float
    total_interest_paid: float
    days_overdue: int
    installments_overdue: int
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AmortizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    loan_id: uuid.UUID
    installment_number: int
    due_date: date
    principal_amount: float
    interest_amount: float
    total_amount: float
    balance_after: float
    paid_amount: float
    paid_date: date | None = None
    status: str


class DisbursementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    loan_id: uuid.UUID
    amount: float
    method: str
    disbursement_date: date
    finance_transaction_id: uuid.UUID | None = None
    notes: str | None = None
