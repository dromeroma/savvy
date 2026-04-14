"""Parking services REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.parking.services.schemas import *
from src.apps.parking.services.service import ParkingServicesService

router = APIRouter(
    prefix="/services",
    tags=["Parking Services"],
    dependencies=[Depends(require_permission("parking", "services.write", "sessions.read"))],
)

@router.get("/types", response_model=list[ServiceTypeResponse])
async def list_types(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ParkingServicesService.list_types(db, org_id)

@router.post("/types", response_model=ServiceTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_type(data: ServiceTypeCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ParkingServicesService.create_type(db, org_id, data)

@router.get("/orders", response_model=list[ServiceOrderResponse])
async def list_orders(session_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ParkingServicesService.list_orders(db, org_id, session_id)

@router.post("/orders", response_model=ServiceOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(data: ServiceOrderCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ParkingServicesService.create_order(db, org_id, data)

@router.post("/orders/{order_id}/complete", response_model=ServiceOrderResponse)
async def complete_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ParkingServicesService.complete_order(db, org_id, order_id)
