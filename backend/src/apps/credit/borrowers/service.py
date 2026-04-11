"""Business logic for SavvyCredit borrowers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.credit.borrowers.models import CreditBorrower
from src.apps.credit.borrowers.schemas import (
    BorrowerCreate,
    BorrowerListParams,
    BorrowerResponse,
    BorrowerUpdate,
)
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate, PersonUpdate
from src.modules.people.service import PeopleService

_PERSON_FIELDS = {
    "first_name", "last_name", "email", "phone", "date_of_birth",
    "gender", "document_type", "document_number", "address", "city",
    "country", "occupation",
}

_CREDIT_FIELDS = {
    "credit_limit", "credit_score", "risk_level", "employer",
    "monthly_income", "notes", "status",
}


def _build_response(borrower: CreditBorrower, person: Person) -> BorrowerResponse:
    return BorrowerResponse(
        id=borrower.id,
        organization_id=borrower.organization_id,
        person_id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        email=person.email,
        phone=person.phone,
        date_of_birth=person.date_of_birth,
        gender=person.gender,
        document_type=person.document_type,
        document_number=person.document_number,
        address=person.address,
        city=person.city,
        occupation=person.occupation,
        photo_url=person.photo_url,
        credit_score=borrower.credit_score,
        credit_limit=float(borrower.credit_limit) if borrower.credit_limit else None,
        risk_level=borrower.risk_level,
        total_borrowed=float(borrower.total_borrowed),
        total_outstanding=float(borrower.total_outstanding),
        total_paid=float(borrower.total_paid),
        active_loans=borrower.active_loans,
        completed_loans=borrower.completed_loans,
        defaulted_loans=borrower.defaulted_loans,
        employer=borrower.employer,
        monthly_income=float(borrower.monthly_income) if borrower.monthly_income else None,
        notes=borrower.notes,
        status=borrower.status,
        created_at=borrower.created_at,
        updated_at=borrower.updated_at,
    )


class BorrowerService:

    @staticmethod
    async def create_borrower(
        db: AsyncSession, org_id: uuid.UUID, data: BorrowerCreate,
    ) -> BorrowerResponse:
        person_data = PersonCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            document_type=data.document_type,
            document_number=data.document_number,
            address=data.address,
            city=data.city,
            country=data.country,
            occupation=data.occupation,
        )
        person = await PeopleService.create_person(db, org_id, person_data)

        borrower = CreditBorrower(
            organization_id=org_id,
            person_id=person.id,
            credit_limit=data.credit_limit,
            employer=data.employer,
            monthly_income=data.monthly_income,
            notes=data.notes,
        )
        db.add(borrower)
        await db.flush()
        await db.refresh(borrower)
        return _build_response(borrower, person)

    @staticmethod
    async def list_borrowers(
        db: AsyncSession, org_id: uuid.UUID, params: BorrowerListParams,
    ) -> tuple[list[BorrowerResponse], int]:
        base = (
            select(CreditBorrower, Person)
            .join(Person, Person.id == CreditBorrower.person_id)
            .where(CreditBorrower.organization_id == org_id, Person.deleted_at.is_(None))
        )
        if params.status:
            base = base.where(CreditBorrower.status == params.status)
        if params.risk_level:
            base = base.where(CreditBorrower.risk_level == params.risk_level)
        if params.search:
            term = f"%{params.search}%"
            base = base.where(or_(
                Person.first_name.ilike(term),
                Person.last_name.ilike(term),
                Person.document_number.ilike(term),
                Person.email.ilike(term),
            ))

        count_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        offset = (params.page - 1) * params.page_size
        result = await db.execute(
            base.order_by(Person.last_name, Person.first_name)
            .offset(offset).limit(params.page_size)
        )
        items = [_build_response(b, p) for b, p in result.all()]
        return items, total

    @staticmethod
    async def get_borrower(
        db: AsyncSession, org_id: uuid.UUID, borrower_id: uuid.UUID,
    ) -> BorrowerResponse:
        result = await db.execute(
            select(CreditBorrower, Person)
            .join(Person, Person.id == CreditBorrower.person_id)
            .where(
                CreditBorrower.id == borrower_id,
                CreditBorrower.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Borrower not found.")
        return _build_response(row[0], row[1])

    @staticmethod
    async def update_borrower(
        db: AsyncSession, org_id: uuid.UUID, borrower_id: uuid.UUID, data: BorrowerUpdate,
    ) -> BorrowerResponse:
        result = await db.execute(
            select(CreditBorrower, Person)
            .join(Person, Person.id == CreditBorrower.person_id)
            .where(
                CreditBorrower.id == borrower_id,
                CreditBorrower.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Borrower not found.")

        borrower, person = row
        update_data = data.model_dump(exclude_unset=True)

        person_updates = {k: v for k, v in update_data.items() if k in _PERSON_FIELDS}
        credit_updates = {k: v for k, v in update_data.items() if k in _CREDIT_FIELDS}

        if person_updates:
            person = await PeopleService.update_person(db, org_id, person.id, PersonUpdate(**person_updates))
        if credit_updates:
            for field, value in credit_updates.items():
                setattr(borrower, field, value)
            await db.flush()
            await db.refresh(borrower)

        return _build_response(borrower, person)
