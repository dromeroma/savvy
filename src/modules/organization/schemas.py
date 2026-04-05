"""Pydantic v2 schemas for the Organization module."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


class OrganizationResponse(BaseModel):
    """Public representation of an organization."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str
    settings: dict
    created_at: datetime
    updated_at: datetime


class OrganizationUpdate(BaseModel):
    """Partial update payload for an organization."""

    name: str | None = None
    settings: dict | None = None


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------


class MemberResponse(BaseModel):
    """Membership enriched with user profile fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    name: str
    role: str
    joined_at: datetime
    created_at: datetime


class InviteMemberRequest(BaseModel):
    """Payload for inviting a new member to the organization."""

    email: EmailStr
    role: Literal["admin", "member"] = Field(default="member")


class UpdateMemberRoleRequest(BaseModel):
    """Payload for changing a member's role."""

    role: Literal["admin", "member", "owner"]


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------


class InvitationResponse(BaseModel):
    """Public representation of an invitation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
