"""Pydantic schemas for pastoral sub-module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------
# Member lifecycle
# -----------------------------------------------------------------

LIFECYCLE_STATUS = Literal[
    "visitor", "attendee", "in_doctrine", "baptized",
    "active_member", "inactive", "transferred", "left", "deceased",
]


class LifecycleCreate(BaseModel):
    congregant_id: uuid.UUID
    person_id: uuid.UUID
    from_status: LIFECYCLE_STATUS | None = None
    to_status: LIFECYCLE_STATUS
    changed_at: datetime | None = None
    changed_by: uuid.UUID | None = None
    reason: str | None = None
    notes: str | None = None


class LifecycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    congregant_id: uuid.UUID
    person_id: uuid.UUID
    from_status: str | None = None
    to_status: str
    changed_at: datetime
    changed_by: uuid.UUID | None = None
    reason: str | None = None
    notes: str | None = None
    created_at: datetime


# -----------------------------------------------------------------
# Transfers
# -----------------------------------------------------------------

TRANSFER_STATUS = Literal["pending", "approved", "completed", "rejected"]


class TransferCreate(BaseModel):
    person_id: uuid.UUID
    from_scope_id: uuid.UUID | None = None
    to_scope_id: uuid.UUID
    transfer_date: date
    reason: str | None = None
    approved_by: uuid.UUID | None = None
    status: TRANSFER_STATUS = "completed"
    notes: str | None = None


class TransferUpdate(BaseModel):
    status: TRANSFER_STATUS | None = None
    approved_by: uuid.UUID | None = None
    notes: str | None = None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID
    from_scope_id: uuid.UUID | None = None
    to_scope_id: uuid.UUID
    transfer_date: date
    reason: str | None = None
    approved_by: uuid.UUID | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------
# Pastoral notes
# -----------------------------------------------------------------

NOTE_TYPE = Literal["observation", "recognition", "discipline", "prayer", "counseling", "other"]
NOTE_VISIBILITY = Literal["private", "pastor", "leadership", "public"]


class PastoralNoteCreate(BaseModel):
    person_id: uuid.UUID
    author_id: uuid.UUID | None = None
    note_type: NOTE_TYPE = "observation"
    visibility: NOTE_VISIBILITY = "pastor"
    title: str | None = Field(None, max_length=200)
    content: str = Field(..., min_length=1)


class PastoralNoteUpdate(BaseModel):
    note_type: NOTE_TYPE | None = None
    visibility: NOTE_VISIBILITY | None = None
    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, min_length=1)


class PastoralNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID
    author_id: uuid.UUID | None = None
    note_type: str
    visibility: str
    title: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime
