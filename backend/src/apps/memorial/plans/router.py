"""Endpoints REST para planes exequiales."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.plans.schemas import (
    PlanCreate,
    PlanListItem,
    PlanResponse,
    PlanUpdate,
)
from src.apps.memorial.plans.service import PlansService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/plans", tags=["Memorial · Planes exequiales"])


@router.get(
    "",
    response_model=list[PlanListItem],
    dependencies=[Depends(require_permission(
        "memorial", "plans.read", "plans.manage", "contracts.read", "contracts.manage",
    ))],
)
async def list_plans(
    active_only: bool = Query(False),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PlansService.list_plans(db, org_id, active_only=active_only, search=search)


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    dependencies=[Depends(require_permission(
        "memorial", "plans.read", "plans.manage", "contracts.manage",
    ))],
)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PlansService.get_plan(db, org_id, plan_id)


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "plans.manage"))],
)
async def create_plan(
    data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PlansService.create_plan(db, org_id, data)


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
    dependencies=[Depends(require_permission("memorial", "plans.manage"))],
)
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PlansService.update_plan(db, org_id, plan_id, data)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("memorial", "plans.manage"))],
)
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await PlansService.delete_plan(db, org_id, plan_id)
