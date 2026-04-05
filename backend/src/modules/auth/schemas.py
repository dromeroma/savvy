"""Pydantic v2 request/response schemas for the Auth module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Payload for registering a new organization and its owner user."""

    org_name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Payload for authenticating an existing user."""

    email: EmailStr
    password: str
    org_id: uuid.UUID | None = None  # Optional: if user has multiple orgs


class RefreshRequest(BaseModel):
    """Payload for refreshing an access token."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Payload for changing the current user's password."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Optional fields for updating the user profile."""

    name: str | None = Field(None, min_length=1, max_length=255)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    """JWT token pair returned after login or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public-facing user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    email_verified_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime


class OrganizationResponse(BaseModel):
    """Minimal organization data included in registration response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str


class OrgWithRole(BaseModel):
    """Organization + user's role in it (for org selector)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str
    role: str


class AuthResponse(BaseModel):
    """Full response returned after successful registration."""

    tokens: TokenResponse
    user: UserResponse
    organization: OrganizationResponse


class LoginResponse(BaseModel):
    """Login response — tokens if single org, org list if multiple."""

    tokens: TokenResponse | None = None
    user: UserResponse
    organization: OrganizationResponse | None = None
    organizations: list[OrgWithRole] | None = None
    requires_org_selection: bool = False
