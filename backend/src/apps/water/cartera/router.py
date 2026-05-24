"""Cartera REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cartera.schemas import (
    AgingReport,
    OverdueSubscriber,
    RecalcResult,
)
from src.apps.water.cartera.service import CarteraService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/cartera", tags=["Water · Cartera"])


@router.post(
    "/recalculate",
    response_model=RecalcResult,
    dependencies=[Depends(require_permission("water", "cartera.manage", "invoices.manage"))],
)
async def recalculate(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Mark past-due invoices as overdue, apply late interest, and sync
    subscriber.status accordingly. Idempotent — safe to run repeatedly."""
    return await CarteraService.recalc_overdue(db, org_id)


@router.get(
    "/aging",
    response_model=AgingReport,
    dependencies=[Depends(require_permission("water", "cartera.read", "cartera.manage", "invoices.read"))],
)
async def aging(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CarteraService.aging_report(db, org_id)


@router.get(
    "/overdue-subscribers",
    response_model=list[OverdueSubscriber],
    dependencies=[Depends(require_permission("water", "cartera.read", "cartera.manage", "invoices.read"))],
)
async def overdue_subscribers(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CarteraService.overdue_subscribers(db, org_id, limit=limit)
