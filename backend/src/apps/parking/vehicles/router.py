"""Parking vehicles REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.parking.vehicles.schemas import VehicleCreate, VehicleResponse
from src.apps.parking.vehicles.service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Parking Vehicles"])

@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(search: str | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await VehicleService.list_vehicles(db, org_id, search)

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await VehicleService.create_vehicle(db, org_id, data)
