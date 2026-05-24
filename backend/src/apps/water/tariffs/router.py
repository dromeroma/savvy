"""Tariffs REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.tariffs.schemas import (
    TariffCreate,
    TariffResponse,
    TariffUpdate,
)
from src.apps.water.tariffs.service import TariffsService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/tariffs", tags=["Water · Tarifas"])


@router.get(
    "",
    response_model=list[TariffResponse],
    dependencies=[Depends(require_permission("water", "tariffs.read", "tariffs.manage"))],
)
async def list_tariffs(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TariffsService.list_tariffs(db, org_id, active_only=active_only)


@router.get(
    "/{tariff_id}",
    response_model=TariffResponse,
    dependencies=[Depends(require_permission("water", "tariffs.read", "tariffs.manage"))],
)
async def get_tariff(
    tariff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TariffsService.get_tariff(db, org_id, tariff_id)


@router.post(
    "",
    response_model=TariffResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "tariffs.manage"))],
)
async def create_tariff(
    data: TariffCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TariffsService.create_tariff(db, org_id, data)


@router.patch(
    "/{tariff_id}",
    response_model=TariffResponse,
    dependencies=[Depends(require_permission("water", "tariffs.manage"))],
)
async def update_tariff(
    tariff_id: uuid.UUID,
    data: TariffUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TariffsService.update_tariff(db, org_id, tariff_id, data)


@router.delete(
    "/{tariff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "tariffs.manage"))],
)
async def delete_tariff(
    tariff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await TariffsService.delete_tariff(db, org_id, tariff_id)
