"""Business logic for SavvyEdu student management.

Delegates person-level operations to PeopleService.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.edu.students.models import EduGuardian, EduStudent
from src.apps.edu.students.schemas import (
    GuardianCreate,
    StudentCreate,
    StudentListParams,
    StudentResponse,
    StudentUpdate,
)
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate, PersonUpdate
from src.modules.people.service import PeopleService

_PERSON_FIELDS = {
    "first_name", "last_name", "email", "phone", "date_of_birth",
    "gender", "document_type", "document_number",
    "country", "state", "city", "address",
}

_STUDENT_FIELDS = {
    "program_id", "curriculum_version_id", "current_period_id", "academic_status",
}


def _build_response(student: EduStudent, person: Person) -> StudentResponse:
    return StudentResponse(
        id=student.id,
        organization_id=student.organization_id,
        person_id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        email=person.email,
        phone=person.phone,
        date_of_birth=person.date_of_birth,
        gender=person.gender,
        document_type=person.document_type,
        document_number=person.document_number,
        country=person.country,
        state=person.state,
        city=person.city,
        address=person.address,
        photo_url=person.photo_url,
        status=person.status,
        student_code=student.student_code,
        program_id=student.program_id,
        curriculum_version_id=student.curriculum_version_id,
        current_period_id=student.current_period_id,
        admission_date=student.admission_date,
        academic_status=student.academic_status,
        cumulative_gpa=float(student.cumulative_gpa) if student.cumulative_gpa else None,
        completed_credits=student.completed_credits,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


class StudentService:
    """CRUD operations for students backed by SavvyPeople."""

    @staticmethod
    async def create_student(
        db: AsyncSession, org_id: uuid.UUID, data: StudentCreate,
    ) -> StudentResponse:
        person_data = PersonCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            document_type=data.document_type,
            document_number=data.document_number,
            country=data.country,
            state=data.state,
            city=data.city,
            address=data.address,
        )
        person = await PeopleService.create_person(db, org_id, person_data)

        student = EduStudent(
            organization_id=org_id,
            person_id=person.id,
            student_code=data.student_code,
            program_id=data.program_id,
            curriculum_version_id=data.curriculum_version_id,
            admission_date=data.admission_date,
        )
        db.add(student)
        await db.flush()
        await db.refresh(student)

        return _build_response(student, person)

    @staticmethod
    async def list_students(
        db: AsyncSession, org_id: uuid.UUID, params: StudentListParams,
    ) -> tuple[list[StudentResponse], int]:
        base = (
            select(EduStudent, Person)
            .join(Person, Person.id == EduStudent.person_id)
            .where(EduStudent.organization_id == org_id, Person.deleted_at.is_(None))
        )

        if params.academic_status:
            base = base.where(EduStudent.academic_status == params.academic_status)
        if params.program_id:
            base = base.where(EduStudent.program_id == params.program_id)
        if params.search:
            term = f"%{params.search}%"
            base = base.where(
                or_(
                    Person.first_name.ilike(term),
                    Person.last_name.ilike(term),
                    Person.email.ilike(term),
                    Person.document_number.ilike(term),
                    EduStudent.student_code.ilike(term),
                )
            )

        count_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        offset = (params.page - 1) * params.page_size
        result = await db.execute(
            base.order_by(Person.last_name, Person.first_name)
            .offset(offset).limit(params.page_size)
        )
        items = [_build_response(s, p) for s, p in result.all()]
        return items, total

    @staticmethod
    async def get_student(
        db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID,
    ) -> StudentResponse:
        result = await db.execute(
            select(EduStudent, Person)
            .join(Person, Person.id == EduStudent.person_id)
            .where(
                EduStudent.id == student_id,
                EduStudent.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Student not found.")
        return _build_response(row[0], row[1])

    @staticmethod
    async def update_student(
        db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID, data: StudentUpdate,
    ) -> StudentResponse:
        result = await db.execute(
            select(EduStudent, Person)
            .join(Person, Person.id == EduStudent.person_id)
            .where(
                EduStudent.id == student_id,
                EduStudent.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Student not found.")

        student, person = row
        update_data = data.model_dump(exclude_unset=True)

        person_updates = {k: v for k, v in update_data.items() if k in _PERSON_FIELDS}
        student_updates = {k: v for k, v in update_data.items() if k in _STUDENT_FIELDS}

        if person_updates:
            person = await PeopleService.update_person(db, org_id, person.id, PersonUpdate(**person_updates))

        if student_updates:
            for field, value in student_updates.items():
                setattr(student, field, value)
            await db.flush()
            await db.refresh(student)

        return _build_response(student, person)

    # ------------------------------------------------------------------
    # Guardians
    # ------------------------------------------------------------------

    @staticmethod
    async def add_guardian(
        db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID, data: GuardianCreate,
    ) -> EduGuardian:
        guardian = EduGuardian(
            organization_id=org_id,
            person_id=data.person_id,
            student_id=student_id,
            relationship=data.relationship,
            is_primary=data.is_primary,
        )
        db.add(guardian)
        await db.flush()
        await db.refresh(guardian)
        return guardian

    @staticmethod
    async def list_guardians(
        db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID,
    ) -> list[EduGuardian]:
        result = await db.execute(
            select(EduGuardian).where(
                EduGuardian.organization_id == org_id,
                EduGuardian.student_id == student_id,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def remove_guardian(
        db: AsyncSession, org_id: uuid.UUID, guardian_id: uuid.UUID,
    ) -> None:
        result = await db.execute(
            select(EduGuardian).where(
                EduGuardian.id == guardian_id,
                EduGuardian.organization_id == org_id,
            )
        )
        guardian = result.scalar_one_or_none()
        if guardian is None:
            raise NotFoundError("Guardian not found.")
        await db.delete(guardian)
        await db.flush()
