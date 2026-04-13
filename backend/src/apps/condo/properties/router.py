"""Condo properties REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.condo.properties.schemas import *
from src.apps.condo.properties.service import PropertyService

router = APIRouter(
    tags=["Condo Properties"],
    dependencies=[Depends(require_permission("condo", "units.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("condo", "units.write"))]


@router.get("/properties", response_model=list[PropertyResponse])
async def list_properties(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PropertyService.list_properties(db, org_id)

@router.post("/properties", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_property(data: PropertyCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PropertyService.create_property(db, org_id, data)

@router.get("/units", response_model=list[UnitResponse])
async def list_units(property_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PropertyService.list_units(db, org_id, property_id)

@router.post("/units", response_model=UnitResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_unit(data: UnitCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PropertyService.create_unit(db, org_id, data)
