"""Health clinical REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.health.clinical.schemas import *
from src.apps.health.clinical.service import ClinicalService

router = APIRouter(prefix="/clinical", tags=["Health Clinical"])

@router.get("/records", response_model=list[ClinicalRecordResponse])
async def list_records(patient_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.list_records(db, org_id, patient_id)

@router.post("/records", response_model=ClinicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(data: ClinicalRecordCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.create_record(db, org_id, data)

@router.post("/vitals", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
async def add_vitals(data: VitalsCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.add_vitals(db, org_id, data)

@router.post("/diagnoses", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def add_diagnosis(data: DiagnosisCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.add_diagnosis(db, org_id, data)

@router.get("/diagnoses", response_model=list[DiagnosisResponse])
async def list_diagnoses(patient_id: uuid.UUID = Query(...), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.list_diagnoses(db, org_id, patient_id)

@router.post("/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def add_prescription(data: PrescriptionCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.add_prescription(db, org_id, data)

@router.get("/prescriptions", response_model=list[PrescriptionResponse])
async def list_prescriptions(patient_id: uuid.UUID = Query(...), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.list_prescriptions(db, org_id, patient_id)

@router.post("/lab-orders", response_model=LabOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_order(data: LabOrderCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.create_lab_order(db, org_id, data)

@router.get("/lab-orders", response_model=list[LabOrderResponse])
async def list_lab_orders(patient_id: uuid.UUID = Query(...), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ClinicalService.list_lab_orders(db, org_id, patient_id)
