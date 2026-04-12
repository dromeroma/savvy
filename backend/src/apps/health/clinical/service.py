"""Business logic for health clinical records."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.health.clinical.models import *
from src.apps.health.clinical.schemas import *


class ClinicalService:
    @staticmethod
    async def create_record(db: AsyncSession, org_id: uuid.UUID, data: ClinicalRecordCreate) -> HealthClinicalRecord:
        r = HealthClinicalRecord(organization_id=org_id, **data.model_dump())
        db.add(r); await db.flush(); await db.refresh(r); return r

    @staticmethod
    async def list_records(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID | None = None) -> list[HealthClinicalRecord]:
        q = select(HealthClinicalRecord).where(HealthClinicalRecord.organization_id == org_id)
        if patient_id: q = q.where(HealthClinicalRecord.patient_id == patient_id)
        return list((await db.execute(q.order_by(HealthClinicalRecord.record_date.desc()))).scalars().all())

    @staticmethod
    async def add_vitals(db: AsyncSession, org_id: uuid.UUID, data: VitalsCreate) -> HealthVitals:
        v = HealthVitals(organization_id=org_id, **data.model_dump())
        db.add(v); await db.flush(); await db.refresh(v); return v

    @staticmethod
    async def add_diagnosis(db: AsyncSession, org_id: uuid.UUID, data: DiagnosisCreate) -> HealthDiagnosis:
        d = HealthDiagnosis(organization_id=org_id, **data.model_dump())
        db.add(d); await db.flush(); await db.refresh(d); return d

    @staticmethod
    async def list_diagnoses(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID) -> list[HealthDiagnosis]:
        return list((await db.execute(select(HealthDiagnosis).where(HealthDiagnosis.organization_id == org_id, HealthDiagnosis.patient_id == patient_id).order_by(HealthDiagnosis.created_at.desc()))).scalars().all())

    @staticmethod
    async def add_prescription(db: AsyncSession, org_id: uuid.UUID, data: PrescriptionCreate) -> HealthPrescription:
        p = HealthPrescription(organization_id=org_id, **data.model_dump())
        db.add(p); await db.flush(); await db.refresh(p); return p

    @staticmethod
    async def list_prescriptions(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID) -> list[HealthPrescription]:
        return list((await db.execute(select(HealthPrescription).where(HealthPrescription.organization_id == org_id, HealthPrescription.patient_id == patient_id).order_by(HealthPrescription.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_lab_order(db: AsyncSession, org_id: uuid.UUID, data: LabOrderCreate) -> HealthLabOrder:
        o = HealthLabOrder(organization_id=org_id, **data.model_dump())
        db.add(o); await db.flush(); await db.refresh(o); return o

    @staticmethod
    async def list_lab_orders(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID) -> list[HealthLabOrder]:
        return list((await db.execute(select(HealthLabOrder).where(HealthLabOrder.organization_id == org_id, HealthLabOrder.patient_id == patient_id).order_by(HealthLabOrder.created_at.desc()))).scalars().all())
