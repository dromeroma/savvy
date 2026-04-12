"""Condo residents and visitors REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.condo.residents.schemas import *
from src.apps.condo.residents.service import ResidentService

router = APIRouter(tags=["Condo Residents"])

@router.get("/residents", response_model=list[ResidentResponse])
async def list_residents(unit_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ResidentService.list_residents(db, org_id, unit_id)

@router.post("/residents", response_model=ResidentResponse, status_code=status.HTTP_201_CREATED)
async def create_resident(data: ResidentCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ResidentService.create_resident(db, org_id, data)

@router.get("/visitors", response_model=list[VisitorResponse])
async def list_visitors(status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ResidentService.list_visitors(db, org_id, status_filter)

@router.post("/visitors", response_model=VisitorResponse, status_code=status.HTTP_201_CREATED)
async def register_visitor(data: VisitorCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ResidentService.register_visitor(db, org_id, data)

@router.post("/visitors/{visitor_id}/exit", response_model=VisitorResponse)
async def exit_visitor(visitor_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ResidentService.exit_visitor(db, org_id, visitor_id)
