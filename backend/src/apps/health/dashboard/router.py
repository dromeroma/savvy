"""Health dashboard REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.health.dashboard.service import HealthDashboardService

router = APIRouter(prefix="/dashboard", tags=["Health Dashboard"])

@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await HealthDashboardService.get_kpis(db, org_id)
