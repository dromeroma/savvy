"""Pydantic schemas for water subscribers."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


SubscriberStatus = Literal["active", "suspended", "overdue", "retired"]
SubscriberType = Literal["residential", "commercial", "industrial", "official"]


class SubscriberBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    business_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    neighborhood: str | None = Field(None, max_length=100)
    city_id: int | None = None
    stratum: int | None = Field(None, ge=1, le=6)
    subscriber_type: SubscriberType = "residential"
    status: SubscriberStatus = "active"
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None
    registered_at: date | None = None


class SubscriberCreate(SubscriberBase):
    pass


class SubscriberUpdate(BaseModel):
    document_type: str | None = None
    document_number: str | None = None
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = None
    business_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    mobile: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    city_id: int | None = None
    stratum: int | None = Field(None, ge=1, le=6)
    subscriber_type: SubscriberType | None = None
    status: SubscriberStatus | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None


class SubscriberResponse(SubscriberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    retired_at: date | None = None
    created_at: datetime
    updated_at: datetime


class SubscriberListItem(BaseModel):
    """Compact row for the subscribers list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    first_name: str
    last_name: str | None
    business_name: str | None
    document_number: str | None
    address: str | None
    neighborhood: str | None
    subscriber_type: str
    status: str
    stratum: int | None
    meter_count: int = 0


class ServiceActionRequest(BaseModel):
    reason: str | None = None
    create_fee_invoice: bool = True


class InvitePortalRequest(BaseModel):
    """Admin invites a subscriber to the customer portal.

    Creates a Savvy user (or reuses the existing one) and assigns the
    'customer' role on the water app, linking water_subscribers.user_id.
    """
    email: str  # used as login
    password: str  # initial password the admin will share
    name: str | None = None  # optional override of the user display name


class InvitePortalResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    name: str
    created_new_user: bool
