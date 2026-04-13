"""Church dashboard endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.church.dashboard.service import ChurchDashboardService

router = APIRouter(prefix="/dashboard", tags=["Church Dashboard"])


@router.get("/kpis")
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Return aggregated KPIs for the church dashboard."""
    return await ChurchDashboardService.get_kpis(db, org_id)


@router.get("/analytics")
async def get_analytics(
    scope_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Return multi-level segmentation + growth analytics.

    When `scope_id` is provided, results are filtered to that scope and
    all its descendants (e.g. country → zones → churches).
    """
    return await ChurchDashboardService.get_analytics(db, org_id, scope_id)


@router.get("/scopes")
async def list_scopes(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Flat list of organizational scopes for the dashboard selector."""
    return await ChurchDashboardService.get_scope_tree(db, org_id)
