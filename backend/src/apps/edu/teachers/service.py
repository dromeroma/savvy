"""Business logic for SavvyEdu teacher management."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.edu.teachers.models import EduTeacher
from src.apps.edu.teachers.schemas import (
    TeacherCreate,
    TeacherListParams,
    TeacherResponse,
    TeacherUpdate,
)
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate, PersonUpdate
from src.modules.people.service import PeopleService

_PERSON_FIELDS = {
    "first_name", "last_name", "email", "phone", "date_of_birth",
    "gender", "document_type", "document_number",
    "country", "state", "city", "address",
}

_TEACHER_FIELDS = {
    "department_scope_id", "specialization", "hire_date", "contract_type", "bio", "status",
}


def _build_response(teacher: EduTeacher, person: Person) -> TeacherResponse:
    return TeacherResponse(
        id=teacher.id,
        organization_id=teacher.organization_id,
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
        employee_code=teacher.employee_code,
        department_scope_id=teacher.department_scope_id,
        specialization=teacher.specialization,
        hire_date=teacher.hire_date,
        contract_type=teacher.contract_type,
        bio=teacher.bio,
        status=teacher.status,
        created_at=teacher.created_at,
        updated_at=teacher.updated_at,
    )


class TeacherService:
    """CRUD operations for teachers backed by SavvyPeople."""

    @staticmethod
    async def create_teacher(
        db: AsyncSession, org_id: uuid.UUID, data: TeacherCreate,
    ) -> TeacherResponse:
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

        teacher = EduTeacher(
            organization_id=org_id,
            person_id=person.id,
            employee_code=data.employee_code,
            department_scope_id=data.department_scope_id,
            specialization=data.specialization,
            hire_date=data.hire_date,
            contract_type=data.contract_type,
            bio=data.bio,
        )
        db.add(teacher)
        await db.flush()
        await db.refresh(teacher)
        return _build_response(teacher, person)

    @staticmethod
    async def list_teachers(
        db: AsyncSession, org_id: uuid.UUID, params: TeacherListParams,
    ) -> tuple[list[TeacherResponse], int]:
        base = (
            select(EduTeacher, Person)
            .join(Person, Person.id == EduTeacher.person_id)
            .where(EduTeacher.organization_id == org_id, Person.deleted_at.is_(None))
        )

        if params.status:
            base = base.where(EduTeacher.status == params.status)
        if params.department_scope_id:
            base = base.where(EduTeacher.department_scope_id == params.department_scope_id)
        if params.search:
            term = f"%{params.search}%"
            base = base.where(
                or_(
                    Person.first_name.ilike(term),
                    Person.last_name.ilike(term),
                    Person.email.ilike(term),
                    EduTeacher.employee_code.ilike(term),
                )
            )

        count_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        offset = (params.page - 1) * params.page_size
        result = await db.execute(
            base.order_by(Person.last_name, Person.first_name)
            .offset(offset).limit(params.page_size)
        )
        items = [_build_response(t, p) for t, p in result.all()]
        return items, total

    @staticmethod
    async def get_teacher(
        db: AsyncSession, org_id: uuid.UUID, teacher_id: uuid.UUID,
    ) -> TeacherResponse:
        result = await db.execute(
            select(EduTeacher, Person)
            .join(Person, Person.id == EduTeacher.person_id)
            .where(
                EduTeacher.id == teacher_id,
                EduTeacher.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Teacher not found.")
        return _build_response(row[0], row[1])

    @staticmethod
    async def update_teacher(
        db: AsyncSession, org_id: uuid.UUID, teacher_id: uuid.UUID, data: TeacherUpdate,
    ) -> TeacherResponse:
        result = await db.execute(
            select(EduTeacher, Person)
            .join(Person, Person.id == EduTeacher.person_id)
            .where(
                EduTeacher.id == teacher_id,
                EduTeacher.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Teacher not found.")

        teacher, person = row
        update_data = data.model_dump(exclude_unset=True)

        person_updates = {k: v for k, v in update_data.items() if k in _PERSON_FIELDS}
        teacher_updates = {k: v for k, v in update_data.items() if k in _TEACHER_FIELDS}

        if person_updates:
            person = await PeopleService.update_person(db, org_id, person.id, PersonUpdate(**person_updates))

        if teacher_updates:
            for field, value in teacher_updates.items():
                setattr(teacher, field, value)
            await db.flush()
            await db.refresh(teacher)

        return _build_response(teacher, person)
