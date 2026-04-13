"""Condo areas REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.condo.areas.schemas import *
from src.apps.condo.areas.service import AreaService

router = APIRouter(
    prefix="/areas",
    tags=["Condo Areas"],
    dependencies=[Depends(require_permission("condo", "amenities.manage", "reports.view"))],
)
_WRITE = [Depends(require_permission("condo", "amenities.manage"))]


@router.get("", response_model=list[CommonAreaResponse])
async def list_areas(property_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AreaService.list_areas(db, org_id, property_id)

@router.post("", response_model=CommonAreaResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_area(data: CommonAreaCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AreaService.create_area(db, org_id, data)

@router.get("/reservations", response_model=list[ReservationResponse])
async def list_reservations(area_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AreaService.list_reservations(db, org_id, area_id)

@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_reservation(data: ReservationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AreaService.create_reservation(db, org_id, data)
