"""Endpoints REST de reportes/analytics."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.reports.schemas import (
    EmployeeRankingReport,
    IncomeReport,
    OperationalKpis,
    PlanRankingReport,
    ServicesByTypeReport,
)
from src.apps.memorial.reports.service import ReportsService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/reports", tags=["Memorial · Reportes"])


def _perm_read():
    return Depends(require_permission(
        "memorial", "reports.read", "reports.manage",
    ))


@router.get("/income", response_model=IncomeReport, dependencies=[_perm_read()])
async def income_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.income_report(db, org_id, date_from, date_to)


@router.get("/services-by-type", response_model=ServicesByTypeReport, dependencies=[_perm_read()])
async def services_by_type(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.services_by_type(db, org_id, date_from, date_to)


@router.get("/plan-ranking", response_model=PlanRankingReport, dependencies=[_perm_read()])
async def plan_ranking(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.plan_ranking(db, org_id)


@router.get("/employee-ranking", response_model=EmployeeRankingReport, dependencies=[_perm_read()])
async def employee_ranking(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.employee_ranking(db, org_id, date_from, date_to)


@router.get("/operational-kpis", response_model=OperationalKpis, dependencies=[_perm_read()])
async def operational_kpis(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.operational_kpis(db, org_id, days=days)
