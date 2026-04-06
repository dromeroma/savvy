"""Pydantic v2 schemas for the Groups module."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Organizational Scopes
# ---------------------------------------------------------------------------


class ScopeCreate(BaseModel):
    """Payload for creating an organizational scope."""

    type: str = Field(..., max_length=30, description="country, zone, district, church")
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    settings: dict = Field(default_factory=dict)


class ScopeUpdate(BaseModel):
    """Partial update payload for an organizational scope."""

    name: str | None = Field(None, max_length=255)
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    settings: dict | None = None


class ScopeResponse(BaseModel):
    """Public representation of an organizational scope."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    name: str
    code: str
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    settings: dict
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Scope Leaders
# ---------------------------------------------------------------------------


class ScopeLeaderCreate(BaseModel):
    """Payload for assigning a leader to a scope."""

    person_id: uuid.UUID
    role: str = Field(..., max_length=50, description="bishop, supervisor, pastor, co_pastor, assistant")
    started_at: date


class ScopeLeaderResponse(BaseModel):
    """Public representation of a scope leader assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    started_at: date
    ended_at: date | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Group Types
# ---------------------------------------------------------------------------


class GroupTypeCreate(BaseModel):
    """Payload for creating a group type."""

    app_code: str | None = Field(None, max_length=50)
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    allow_hierarchy: bool = False
    requires_classes: bool = False
    requires_attendance: bool = False
    requires_activities: bool = False
    max_members: int | None = None
    settings: dict = Field(default_factory=dict)


class GroupTypeResponse(BaseModel):
    """Public representation of a group type."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    app_code: str | None = None
    name: str
    code: str
    allow_hierarchy: bool
    requires_classes: bool
    requires_attendance: bool
    requires_activities: bool
    max_members: int | None = None
    settings: dict
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


class GroupCreate(BaseModel):
    """Payload for creating a group."""

    group_type_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str = Field(..., max_length=255)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    settings: dict = Field(default_factory=dict)


class GroupUpdate(BaseModel):
    """Partial update payload for a group."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    scope_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    status: str | None = Field(None, max_length=20)
    settings: dict | None = None


class GroupResponse(BaseModel):
    """Public representation of a group."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    group_type_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    parent_id: uuid.UUID | None = None
    leader_id: uuid.UUID | None = None
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Group Members
# ---------------------------------------------------------------------------


class GroupMemberAdd(BaseModel):
    """Payload for adding a member to a group."""

    person_id: uuid.UUID
    role: str = Field(default="member", max_length=50, description="leader, assistant, member")


class GroupMemberResponse(BaseModel):
    """Public representation of a group membership."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    group_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    joined_at: datetime
    left_at: datetime | None = None
