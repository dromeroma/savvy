"""Parking infrastructure REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.parking.infrastructure.schemas import *
from src.apps.parking.infrastructure.service import InfrastructureService

router = APIRouter(tags=["Parking Infrastructure"])

@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.list_locations(db, org_id)

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(data: LocationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.create_location(db, org_id, data)

@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(location_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.list_zones(db, org_id, location_id)

@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(data: ZoneCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.create_zone(db, org_id, data)

@router.get("/spots", response_model=list[SpotResponse])
async def list_spots(zone_id: uuid.UUID | None = Query(None), status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.list_spots(db, org_id, zone_id, status_filter)

@router.post("/spots", response_model=SpotResponse, status_code=status.HTTP_201_CREATED)
async def create_spot(data: SpotCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await InfrastructureService.create_spot(db, org_id, data)
