"""Pydantic v2 schemas for SavvyCredit applications."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

APP_STATUS = Literal["pending", "under_review", "approved", "rejected", "cancelled"]


class ApplicationCreate(BaseModel):
    borrower_id: uuid.UUID
    product_id: uuid.UUID
    requested_amount: float = Field(..., gt=0)
    requested_term: int = Field(..., ge=1)
    purpose: str | None = Field(None, max_length=200)
    application_date: date | None = None


class ApplicationDecision(BaseModel):
    status: Literal["approved", "rejected"]
    decision_notes: str | None = None
    approved_amount: float | None = Field(None, gt=0)
    approved_term: int | None = Field(None, ge=1)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    borrower_id: uuid.UUID
    product_id: uuid.UUID
    requested_amount: float
    requested_term: int
    purpose: str | None = None
    application_date: date
    status: str
    reviewed_by: uuid.UUID | None = None
    decision_notes: str | None = None
    approved_amount: float | None = None
    approved_term: int | None = None
    documents: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
