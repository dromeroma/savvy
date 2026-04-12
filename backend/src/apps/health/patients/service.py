"""Business logic for health patients."""

from __future__ import annotations
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.health.patients.models import HealthInsurance, HealthPatient
from src.apps.health.patients.schemas import InsuranceCreate, PatientCreate, PatientResponse, PatientUpdate
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate
from src.modules.people.service import PeopleService

_PERSON_FIELDS = {"first_name", "last_name", "email", "phone", "date_of_birth", "gender", "document_type", "document_number", "address", "city"}


def _build(patient: HealthPatient, person: Person) -> PatientResponse:
    return PatientResponse(id=patient.id, organization_id=patient.organization_id, person_id=person.id,
        first_name=person.first_name, last_name=person.last_name, email=person.email, phone=person.phone,
        date_of_birth=person.date_of_birth, gender=person.gender, document_type=person.document_type,
        document_number=person.document_number, patient_code=patient.patient_code, blood_type=patient.blood_type,
        allergies=patient.allergies or [], chronic_conditions=patient.chronic_conditions or [],
        current_medications=patient.current_medications or [], notes=patient.notes, status=patient.status,
        created_at=patient.created_at)


class PatientService:
    @staticmethod
    async def create_patient(db: AsyncSession, org_id: uuid.UUID, data: PatientCreate) -> PatientResponse:
        person = await PeopleService.create_person(db, org_id, PersonCreate(
            first_name=data.first_name, last_name=data.last_name, email=data.email, phone=data.phone,
            date_of_birth=data.date_of_birth, gender=data.gender, document_type=data.document_type,
            document_number=data.document_number, address=data.address, city=data.city))
        patient = HealthPatient(organization_id=org_id, person_id=person.id, patient_code=data.patient_code,
            blood_type=data.blood_type, allergies=data.allergies, chronic_conditions=data.chronic_conditions)
        db.add(patient); await db.flush(); await db.refresh(patient)
        return _build(patient, person)

    @staticmethod
    async def list_patients(db: AsyncSession, org_id: uuid.UUID, search: str | None = None, page: int = 1, page_size: int = 50) -> tuple[list[PatientResponse], int]:
        base = select(HealthPatient, Person).join(Person, Person.id == HealthPatient.person_id).where(HealthPatient.organization_id == org_id, Person.deleted_at.is_(None))
        if search:
            t = f"%{search}%"
            base = base.where(or_(Person.first_name.ilike(t), Person.last_name.ilike(t), Person.document_number.ilike(t)))
        count = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count.scalar() or 0
        result = await db.execute(base.order_by(Person.last_name).offset((page-1)*page_size).limit(page_size))
        return [_build(p, pe) for p, pe in result.all()], total

    @staticmethod
    async def get_patient(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID) -> PatientResponse:
        result = await db.execute(select(HealthPatient, Person).join(Person, Person.id == HealthPatient.person_id).where(HealthPatient.id == patient_id, HealthPatient.organization_id == org_id))
        row = result.one_or_none()
        if row is None: raise NotFoundError("Patient not found.")
        return _build(row[0], row[1])

    @staticmethod
    async def update_patient(db: AsyncSession, org_id: uuid.UUID, patient_id: uuid.UUID, data: PatientUpdate) -> PatientResponse:
        result = await db.execute(select(HealthPatient, Person).join(Person, Person.id == HealthPatient.person_id).where(HealthPatient.id == patient_id, HealthPatient.organization_id == org_id))
        row = result.one_or_none()
        if row is None: raise NotFoundError("Patient not found.")
        patient, person = row
        for f, v in data.model_dump(exclude_unset=True).items(): setattr(patient, f, v)
        await db.flush(); await db.refresh(patient)
        return _build(patient, person)

    @staticmethod
    async def add_insurance(db: AsyncSession, org_id: uuid.UUID, data: InsuranceCreate) -> HealthInsurance:
        ins = HealthInsurance(organization_id=org_id, **data.model_dump())
        db.add(ins); await db.flush(); await db.refresh(ins); return ins
