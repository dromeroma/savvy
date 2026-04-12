"""Condo maintenance REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.condo.maintenance.schemas import MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate
from src.apps.condo.maintenance.service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Condo Maintenance"])

@router.get("", response_model=list[MaintenanceResponse])
async def list_requests(status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await MaintenanceService.list_requests(db, org_id, status_filter)

@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_request(data: MaintenanceCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await MaintenanceService.create_request(db, org_id, data)

@router.patch("/{req_id}", response_model=MaintenanceResponse)
async def update_request(req_id: uuid.UUID, data: MaintenanceUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await MaintenanceService.update_request(db, org_id, req_id, data)
