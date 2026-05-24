"""Zone overview endpoints — authenticated, gated on church_zone_leaders."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.zone.schemas import ZoneOverviewResponse
from src.apps.church.zone.service import zone_overview_service
from src.core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/zone", tags=["Church Zone"])


@router.get(
    "/overview",
    response_model=ZoneOverviewResponse,
    summary="Aggregate metrics for the churches in the leader's zone",
)
async def get_zone_overview(
    request: Request,
    zone_id: uuid.UUID | None = Query(
        None,
        description="Zone to inspect. Defaults to the first zone the user leads.",
    ),
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> ZoneOverviewResponse:
    user_id = uuid.UUID(user["sub"])
    platform_roles = user.get("platform_roles") or []
    is_super_admin = isinstance(platform_roles, list) and "super_admin" in platform_roles

    user_org_id: uuid.UUID | None = getattr(request.state, "org_id", None)

    return await zone_overview_service.get_overview(
        db,
        user_id=user_id,
        user_org_id=user_org_id,
        zone_id=zone_id,
        is_super_admin=is_super_admin,
    )
