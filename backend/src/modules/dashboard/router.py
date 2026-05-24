"""Dashboard endpoint — returns the org's strategic summary."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.dashboard.schemas import DashboardSummaryResponse
from src.modules.dashboard.service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Strategic summary for the current org admin",
)
async def get_dashboard_summary(
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryResponse:
    return await dashboard_service.get_summary(db, org_id, uuid.UUID(user["sub"]))
