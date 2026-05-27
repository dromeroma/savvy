"""Schemas Pydantic para CRM (leads + comunicaciones)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


LeadSource = Literal[
    "referral", "walk_in", "web", "social", "whatsapp", "phone", "event", "other"
]
LeadInterest = Literal[
    "exequial_plan", "service_immediate", "service_future", "info", "other"
]
LeadStatus = Literal["new", "contacted", "qualified", "proposal", "won", "lost"]
LeadPriority = Literal["low", "medium", "high", "urgent"]

CommChannel = Literal["call", "email", "whatsapp", "visit", "sms", "meeting", "note"]
CommDirection = Literal["inbound", "outbound", "internal"]


# ---------------------------------------------------------------- Leads


class LeadBase(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    business_name: str | None = Field(None, max_length=200)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    source: LeadSource = "walk_in"
    interest: LeadInterest = "info"
    priority: LeadPriority = "medium"
    assigned_to: uuid.UUID | None = None
    next_follow_up_at: datetime | None = None
    notes: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    business_name: str | None = Field(None, max_length=200)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    source: LeadSource | None = None
    interest: LeadInterest | None = None
    status: LeadStatus | None = None
    priority: LeadPriority | None = None
    assigned_to: uuid.UUID | None = None
    next_follow_up_at: datetime | None = None
    notes: str | None = None
    lost_reason: str | None = Field(None, max_length=255)


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    consecutive: int
    code: str
    status: LeadStatus
    converted_contract_id: uuid.UUID | None = None
    converted_service_id: uuid.UUID | None = None
    converted_at: datetime | None = None
    lost_reason: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class LeadListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    first_name: str | None = None
    last_name: str | None = None
    business_name: str | None = None
    email: str | None = None
    mobile: str | None = None
    phone: str | None = None
    source: LeadSource
    interest: LeadInterest
    status: LeadStatus
    priority: LeadPriority
    assigned_to: uuid.UUID | None = None
    next_follow_up_at: datetime | None = None
    created_at: datetime


# ---------------------------------------------------------------- Communications


class CommunicationBase(BaseModel):
    channel: CommChannel
    direction: CommDirection = "outbound"
    subject: str | None = Field(None, max_length=255)
    content: str | None = None
    occurred_at: datetime | None = None
    outcome: str | None = Field(None, max_length=40)


class CommunicationCreate(CommunicationBase):
    pass


class CommunicationResponse(CommunicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    lead_id: uuid.UUID
    occurred_at: datetime
    created_by: uuid.UUID | None = None
    created_at: datetime


# ---------------------------------------------------------------- Conversion


class ConvertToContract(BaseModel):
    contract_id: uuid.UUID


class ConvertToService(BaseModel):
    service_id: uuid.UUID


class MarkLost(BaseModel):
    lost_reason: str = Field(..., min_length=1, max_length=255)
