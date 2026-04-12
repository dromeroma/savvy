"""POS dashboard REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.pos.dashboard.service import PosDashboardService

router = APIRouter(prefix="/dashboard", tags=["POS Dashboard"])

@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PosDashboardService.get_kpis(db, org_id)
