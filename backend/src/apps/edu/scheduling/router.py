"""SavvyEdu scheduling REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.scheduling.schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    ScheduleCreate,
    ScheduleResponse,
)
from src.apps.edu.scheduling.service import SchedulingService

router = APIRouter(prefix="/scheduling", tags=["Edu Scheduling"])


# Rooms
@router.get("/rooms", response_model=list[RoomResponse])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SchedulingService.list_rooms(db, org_id)


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SchedulingService.create_room(db, org_id, data)


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: uuid.UUID,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SchedulingService.update_room(db, org_id, room_id, data)


# Schedules
@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    section_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SchedulingService.list_schedules(db, section_id)


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SchedulingService.create_schedule(db, org_id, data)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await SchedulingService.delete_schedule(db, schedule_id)
