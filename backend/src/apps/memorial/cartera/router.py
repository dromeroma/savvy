"""Endpoints REST de cartera y mora."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.cartera.schemas import (
    AgingReport,
    OverdueDebtor,
    RecalcResult,
)
from src.apps.memorial.cartera.service import CarteraService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/cartera", tags=["Memorial · Cartera"])


@router.post(
    "/recalculate",
    response_model=RecalcResult,
    dependencies=[Depends(require_permission("memorial", "cartera.manage"))],
)
async def recalculate(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CarteraService.recalc_overdue(db, org_id)


@router.get(
    "/aging",
    response_model=AgingReport,
    dependencies=[Depends(require_permission(
        "memorial", "cartera.read", "cartera.manage",
    ))],
)
async def aging(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CarteraService.aging_report(db, org_id)


@router.get(
    "/overdue",
    response_model=list[OverdueDebtor],
    dependencies=[Depends(require_permission(
        "memorial", "cartera.read", "cartera.manage",
    ))],
)
async def overdue(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CarteraService.overdue_debtors(db, org_id, limit=limit)
