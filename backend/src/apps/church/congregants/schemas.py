"""Pydantic v2 schemas for church congregants.

The create/update schemas accept both person fields (forwarded to SavvyPeople)
and church-specific fields (stored in church_congregants).  The response schema
combines both into a flat object for API consumers.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Person field subsets (used for delegation to PeopleService)
# ---------------------------------------------------------------------------

SPIRITUAL_STATUS = Literal["new_believer", "growing", "mature", "leader"]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class CongregantCreate(BaseModel):
    """Payload for creating a congregant (person + church data)."""

    # Person fields
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    occupation: str | None = Field(None, max_length=100)

    # Church-specific fields
    scope_id: uuid.UUID | None = None
    membership_date: date | None = None
    baptism_date: date | None = None
    holy_spirit_baptism: bool = False
    conversion_date: date | None = None
    spiritual_status: SPIRITUAL_STATUS | None = None
    referred_by: uuid.UUID | None = None
    pastoral_notes: str | None = None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class CongregantUpdate(BaseModel):
    """Partial update for a congregant. All fields are optional."""

    # Person fields
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    occupation: str | None = Field(None, max_length=100)
    status: Literal["active", "inactive", "transferred"] | None = None

    # Church-specific fields
    scope_id: uuid.UUID | None = None
    membership_date: date | None = None
    baptism_date: date | None = None
    holy_spirit_baptism: bool | None = None
    conversion_date: date | None = None
    spiritual_status: SPIRITUAL_STATUS | None = None
    referred_by: uuid.UUID | None = None
    pastoral_notes: str | None = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class CongregantResponse(BaseModel):
    """Public representation combining person + church data."""

    model_config = ConfigDict(from_attributes=True)

    # Congregant record identifiers
    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID

    # Person fields (flattened)
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    photo_url: str | None = None
    status: str

    occupation: str | None = None

    # Church-specific fields
    scope_id: uuid.UUID | None = None
    membership_date: date | None = None
    baptism_date: date | None = None
    holy_spirit_baptism: bool = False
    conversion_date: date | None = None
    spiritual_status: str | None = None
    referred_by: uuid.UUID | None = None
    pastoral_notes: str | None = None

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# List params
# ---------------------------------------------------------------------------


class CongregantListParams(BaseModel):
    """Query parameters for listing congregants."""

    status: str | None = None
    search: str | None = None
    spiritual_status: SPIRITUAL_STATUS | None = None
    scope_id: uuid.UUID | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
