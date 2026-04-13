"""SavvyCredit dashboard REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.dashboard.service import CreditDashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Credit Dashboard"],
    dependencies=[Depends(require_permission("credit", "reports.view"))],
)


@router.get("/kpis")
async def get_kpis(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CreditDashboardService.get_kpis(db, org_id)
