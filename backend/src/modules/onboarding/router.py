"""Public onboarding endpoints — no auth required (signup wizard)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.modules.onboarding.schemas import (
    BusinessTypeResponse,
    DenominationResponse,
    ZoneResponse,
)
from src.modules.onboarding.service import onboarding_service

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get(
    "/business-types",
    response_model=list[BusinessTypeResponse],
    summary="List selectable business verticals for signup",
)
async def list_business_types(
    db: AsyncSession = Depends(get_db),
) -> list[BusinessTypeResponse]:
    rows = await onboarding_service.list_business_types(db)
    return [BusinessTypeResponse.model_validate(r) for r in rows]


@router.get(
    "/denominations",
    response_model=list[DenominationResponse],
    summary="List system religious denominations",
)
async def list_denominations(
    business_type: str | None = Query(None, description="Filter by vertical (only 'church' is relevant)"),
    db: AsyncSession = Depends(get_db),
) -> list[DenominationResponse]:
    rows = await onboarding_service.list_denominations(db, business_type)
    return [DenominationResponse.model_validate(r) for r in rows]


@router.get(
    "/zones",
    response_model=list[ZoneResponse],
    summary="List zones of a denomination",
)
async def list_zones(
    denomination_id: uuid.UUID = Query(..., description="Denomination UUID"),
    db: AsyncSession = Depends(get_db),
) -> list[ZoneResponse]:
    rows = await onboarding_service.list_zones(db, denomination_id)
    return [ZoneResponse.model_validate(r) for r in rows]
