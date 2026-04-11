"""Pydantic v2 schemas for SavvyCRM contacts and companies."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

LIFECYCLE = Literal["subscriber", "lead", "qualified_lead", "opportunity", "customer", "evangelist"]


class ContactCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    city: str | None = Field(None, max_length=100)
    source: str | None = Field(None, max_length=50)
    lifecycle_stage: LIFECYCLE = "subscriber"
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    company_id: uuid.UUID | None = None
    company_role: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    source: str | None = Field(None, max_length=50)
    lifecycle_stage: LIFECYCLE | None = None
    lead_score: int | None = Field(None, ge=0)
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    status: Literal["active", "inactive"] | None = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    document_number: str | None = None
    city: str | None = None
    photo_url: str | None = None
    source: str | None = None
    lifecycle_stage: str
    lead_score: int
    tags: list[str]
    custom_fields: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=300)
    phone: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=10)
    size: Literal["startup", "small", "medium", "large", "enterprise"] | None = None
    annual_revenue: float | None = Field(None, ge=0)


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    industry: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=300)
    phone: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    size: str | None = None
    annual_revenue: float | None = Field(None, ge=0)
    status: Literal["active", "inactive"] | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    country: str | None = None
    size: str | None = None
    annual_revenue: float | None = None
    tags: list[str]
    status: str
    created_at: datetime
