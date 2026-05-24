"""Pydantic schemas for the zone overview endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ZoneLeadership(BaseModel):
    """A zone the current user leads."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    name: str | None
    denomination_name: str
    role: str  # 'presbitero' | 'lider'


class ChurchMetrics(BaseModel):
    """Aggregate (non-row-level) metrics for one church."""

    active_congregants: int
    visitors_last_30d: int
    events_last_30d: int
    new_congregants_this_month: int
    income_this_month: Decimal


class ZoneChurch(BaseModel):
    """One church in the zone with its aggregate metrics."""

    id: uuid.UUID
    name: str
    slug: str
    is_mine: bool
    metrics: ChurchMetrics


class ZoneOverviewResponse(BaseModel):
    """Full payload for the zone overview screen."""

    available_zones: list[ZoneLeadership]
    selected_zone: ZoneLeadership | None
    churches: list[ZoneChurch]
