"""Health patients REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.health.patients.schemas import *
from src.apps.health.patients.service import PatientService

router = APIRouter(prefix="/patients", tags=["Health Patients"])

@router.get("", response_model=dict)
async def list_patients(search: str | None = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    items, total = await PatientService.list_patients(db, org_id, search, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PatientService.create_patient(db, org_id, data)

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PatientService.get_patient(db, org_id, patient_id)

@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: uuid.UUID, data: PatientUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PatientService.update_patient(db, org_id, patient_id, data)

@router.post("/insurance", response_model=InsuranceResponse, status_code=status.HTTP_201_CREATED)
async def add_insurance(data: InsuranceCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PatientService.add_insurance(db, org_id, data)
