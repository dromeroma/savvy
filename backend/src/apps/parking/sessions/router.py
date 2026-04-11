"""Parking sessions REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.parking.sessions.schemas import *
from src.apps.parking.sessions.service import SessionService

router = APIRouter(prefix="/sessions", tags=["Parking Sessions"])

@router.post("/entry", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def register_entry(data: SessionEntryCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.entry(db, org_id, data)

@router.post("/{session_id}/exit", response_model=SessionResponse)
async def register_exit(session_id: uuid.UUID, data: SessionExitCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.exit(db, org_id, session_id, data)

@router.get("/active", response_model=list[SessionResponse])
async def list_active(location_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.list_active(db, org_id, location_id)

@router.get("/completed", response_model=list[SessionResponse])
async def list_completed(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.list_completed(db, org_id)

@router.get("/reservations", response_model=list[ReservationResponse])
async def list_reservations(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.list_reservations(db, org_id)

@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(data: ReservationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SessionService.create_reservation(db, org_id, data)
