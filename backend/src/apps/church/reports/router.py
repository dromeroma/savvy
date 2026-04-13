"""Church reports REST endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.reports.schemas import MonthlySummaryResponse, TitheOfTitheResponse
from src.apps.church.reports.service import ChurchReportService

router = APIRouter(
    prefix="/reports",
    tags=["Church Reports"],
    dependencies=[Depends(require_permission("church", "reports.view"))],
)


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def monthly_summary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> MonthlySummaryResponse:
    """Get consolidated monthly report: income, expenses, net, tithe of tithe."""
    return await ChurchReportService.monthly_summary(db, org_id, year, month)


@router.get("/tithe-of-tithe", response_model=TitheOfTitheResponse)
async def tithe_of_tithe(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> TitheOfTitheResponse:
    """Calculate tithe of tithe: 10% of (tithes + offerings) for the period."""
    return await ChurchReportService.tithe_of_tithe(db, org_id, year, month)
