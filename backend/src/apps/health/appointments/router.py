"""Health appointments REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.health.appointments.schemas import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from src.apps.health.appointments.service import AppointmentService

router = APIRouter(
    prefix="/appointments",
    tags=["Health Appointments"],
    dependencies=[Depends(require_permission("health", "appointments.write", "appointments.read"))],
)

@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(provider_id: uuid.UUID | None = Query(None), patient_id: uuid.UUID | None = Query(None), status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AppointmentService.list_appointments(db, org_id, provider_id, patient_id, status_filter)

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(data: AppointmentCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AppointmentService.create_appointment(db, org_id, data)

@router.patch("/{apt_id}", response_model=AppointmentResponse)
async def update_appointment(apt_id: uuid.UUID, data: AppointmentUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await AppointmentService.update_appointment(db, org_id, apt_id, data)
