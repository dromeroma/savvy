"""Pydantic v2 schemas for church members."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ChurchMemberCreate(BaseModel):
    """Payload for creating a church member."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    address: str | None = None
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    membership_date: date | None = None
    notes: str | None = None


class ChurchMemberUpdate(BaseModel):
    """Partial update for a church member."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    membership_date: date | None = None
    status: Literal["active", "inactive", "transferred"] | None = None
    notes: str | None = None


class ChurchMemberResponse(BaseModel):
    """Public representation of a church member."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    membership_date: date | None = None
    status: str
    notes: str | None = None
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ChurchMemberListParams(BaseModel):
    """Query params for listing members."""

    status: str | None = None
    search: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
