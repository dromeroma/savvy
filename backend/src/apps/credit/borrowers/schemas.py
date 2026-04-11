"""Pydantic v2 schemas for SavvyCredit borrowers."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

RISK_LEVEL = Literal["low", "medium", "high", "very_high"]


class BorrowerCreate(BaseModel):
    # Person fields
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=10)
    occupation: str | None = Field(None, max_length=100)
    # Credit fields
    credit_limit: float | None = Field(None, ge=0)
    employer: str | None = Field(None, max_length=200)
    monthly_income: float | None = Field(None, ge=0)
    notes: str | None = None


class BorrowerUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    occupation: str | None = Field(None, max_length=100)
    credit_limit: float | None = Field(None, ge=0)
    credit_score: int | None = Field(None, ge=0)
    risk_level: RISK_LEVEL | None = None
    employer: str | None = Field(None, max_length=200)
    monthly_income: float | None = Field(None, ge=0)
    notes: str | None = None
    status: Literal["active", "blocked", "blacklisted"] | None = None


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID
    # Person fields
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    address: str | None = None
    city: str | None = None
    occupation: str | None = None
    photo_url: str | None = None
    # Credit fields
    credit_score: int | None = None
    credit_limit: float | None = None
    risk_level: str
    total_borrowed: float
    total_outstanding: float
    total_paid: float
    active_loans: int
    completed_loans: int
    defaulted_loans: int
    employer: str | None = None
    monthly_income: float | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class BorrowerListParams(BaseModel):
    search: str | None = None
    risk_level: RISK_LEVEL | None = None
    status: Literal["active", "blocked", "blacklisted"] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)


class GuarantorCreate(BaseModel):
    person_id: uuid.UUID
    relationship: str | None = Field(None, max_length=50)
    guarantee_amount: float | None = Field(None, ge=0)


class GuarantorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    loan_id: uuid.UUID
    person_id: uuid.UUID
    relationship: str | None = None
    guarantee_amount: float | None = None
    status: str
