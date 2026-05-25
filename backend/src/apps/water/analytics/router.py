"""Analytics REST endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.analytics.schemas import AnalyticsResponse
from src.apps.water.analytics.service import AnalyticsService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/analytics", tags=["Water · Analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsResponse,
    dependencies=[Depends(require_permission("water", "analytics.read", "dashboard.view"))],
)
async def overview(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AnalyticsService.overview(db, org_id)
