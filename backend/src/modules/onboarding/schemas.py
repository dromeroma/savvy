"""Pydantic v2 schemas for the onboarding (signup-wizard) endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class BusinessTypeResponse(BaseModel):
    """A selectable business vertical (iglesia, supermercado, etc.)."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str | None = None
    default_app_code: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int


class DenominationResponse(BaseModel):
    """A religious denomination available during signup."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    is_system: bool


class ZoneResponse(BaseModel):
    """A zone inside a denomination."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    name: str | None = None
