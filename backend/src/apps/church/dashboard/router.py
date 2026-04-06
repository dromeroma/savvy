"""Church dashboard endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
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
