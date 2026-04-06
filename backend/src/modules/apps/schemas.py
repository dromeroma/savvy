"""Pydantic v2 schemas for the Apps module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


class AppCatalogResponse(BaseModel):
    """Public representation of an app in the catalog."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    is_active: bool
    is_external: bool = False
    external_url: str | None = None


# ---------------------------------------------------------------------------
# My Apps
# ---------------------------------------------------------------------------


class MyAppResponse(BaseModel):
    """An app the organization has, enriched with the user's role."""

    model_config = ConfigDict(from_attributes=True)

    app: AppCatalogResponse
    role: str | None = None
    status: str
    activated_at: datetime
    trial_ends_at: datetime | None = None
    expires_at: datetime | None = None


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------


class ActivateAppRequest(BaseModel):
    """Payload for activating an app for the organization."""

    app_code: str


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class AssignRoleRequest(BaseModel):
    """Payload for assigning a role to a user in an app."""

    user_id: uuid.UUID
    role: str


class AppUserRoleResponse(BaseModel):
    """Public representation of a user's role in an app."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    app_id: uuid.UUID
    role: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Organization App
# ---------------------------------------------------------------------------


class OrganizationAppResponse(BaseModel):
    """Public representation of an organization's app subscription."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    app_code: str
    app_name: str
    status: str
    activated_at: datetime
    trial_ends_at: datetime | None = None
