"""Pydantic v2 schemas for the SavvyPeople module."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------


class PersonCreate(BaseModel):
    """Payload for creating a new person."""

    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    second_last_name: str | None = Field(None, max_length=100)
    scope_id: uuid.UUID | None = None
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=10)
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=20)
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    marital_status: str | None = Field(None, max_length=20)
    occupation: str | None = Field(None, max_length=100)
    tags: list[str] | None = None


class PersonUpdate(BaseModel):
    """Partial update payload for a person. All fields are optional."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    second_last_name: str | None = Field(None, max_length=100)
    scope_id: uuid.UUID | None = None
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=10)
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=20)
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    marital_status: str | None = Field(None, max_length=20)
    occupation: str | None = Field(None, max_length=100)
    photo_url: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    status: str | None = Field(None, max_length=30)


class PersonResponse(BaseModel):
    """Public representation of a person."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    first_name: str
    last_name: str
    second_last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    photo_url: str | None = None
    tags: list = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime


class PersonListParams(BaseModel):
    """Query parameters for listing people."""

    status: str | None = None
    search: str | None = None
    tags: list[str] | None = None
    scope_id: uuid.UUID | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Family Relationships
# ---------------------------------------------------------------------------


class FamilyRelationshipCreate(BaseModel):
    """Payload for adding a family relationship."""

    related_to: uuid.UUID
    relationship: str = Field(..., max_length=30)


class FamilyRelationshipResponse(BaseModel):
    """Public representation of a family relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    related_to: uuid.UUID
    related_person_name: str
    relationship: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Emergency Contacts
# ---------------------------------------------------------------------------


class EmergencyContactCreate(BaseModel):
    """Payload for adding an emergency contact."""

    name: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=50)
    relationship: str | None = Field(None, max_length=50)


class EmergencyContactResponse(BaseModel):
    """Public representation of an emergency contact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str
    relationship: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class PersonStatsResponse(BaseModel):
    """Aggregate statistics for people within an organization."""

    total: int
    active: int
    inactive: int
    by_gender: dict[str, int]
    by_marital_status: dict[str, int]
