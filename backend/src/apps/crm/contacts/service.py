"""Business logic for SavvyCRM contacts and companies."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.crm.contacts.models import CrmCompany, CrmContact, CrmContactCompany
from src.apps.crm.contacts.schemas import (
    CompanyCreate, CompanyUpdate, ContactCreate, ContactResponse, ContactUpdate,
)
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate, PersonUpdate
from src.modules.people.service import PeopleService

_PERSON_FIELDS = {
    "first_name", "last_name", "email", "phone", "document_type",
    "document_number", "city",
}
_CRM_FIELDS = {
    "source", "lifecycle_stage", "lead_score", "tags", "custom_fields", "status",
}


def _build_contact(contact: CrmContact, person: Person) -> ContactResponse:
    return ContactResponse(
        id=contact.id, organization_id=contact.organization_id, person_id=person.id,
        first_name=person.first_name, last_name=person.last_name,
        email=person.email, phone=person.phone,
        document_number=person.document_number, city=person.city,
        photo_url=person.photo_url,
        source=contact.source, lifecycle_stage=contact.lifecycle_stage,
        lead_score=contact.lead_score, tags=contact.tags or [],
        custom_fields=contact.custom_fields or {},
        status=contact.status, created_at=contact.created_at, updated_at=contact.updated_at,
    )


class ContactService:

    @staticmethod
    async def create_contact(db: AsyncSession, org_id: uuid.UUID, data: ContactCreate) -> ContactResponse:
        person = await PeopleService.create_person(db, org_id, PersonCreate(
            first_name=data.first_name, last_name=data.last_name,
            email=data.email, phone=data.phone,
            document_type=data.document_type, document_number=data.document_number,
            city=data.city,
        ))
        contact = CrmContact(
            organization_id=org_id, person_id=person.id,
            source=data.source, lifecycle_stage=data.lifecycle_stage,
            tags=data.tags, custom_fields=data.custom_fields,
        )
        db.add(contact)
        await db.flush()
        if data.company_id:
            link = CrmContactCompany(contact_id=contact.id, company_id=data.company_id, role=data.company_role, is_primary=True)
            db.add(link)
            await db.flush()
        await db.refresh(contact)
        return _build_contact(contact, person)

    @staticmethod
    async def list_contacts(
        db: AsyncSession, org_id: uuid.UUID,
        search: str | None = None, lifecycle: str | None = None,
        page: int = 1, page_size: int = 50,
    ) -> tuple[list[ContactResponse], int]:
        base = (
            select(CrmContact, Person).join(Person, Person.id == CrmContact.person_id)
            .where(CrmContact.organization_id == org_id, Person.deleted_at.is_(None))
        )
        if lifecycle:
            base = base.where(CrmContact.lifecycle_stage == lifecycle)
        if search:
            t = f"%{search}%"
            base = base.where(or_(Person.first_name.ilike(t), Person.last_name.ilike(t), Person.email.ilike(t)))
        count = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count.scalar() or 0
        result = await db.execute(base.order_by(Person.last_name).offset((page - 1) * page_size).limit(page_size))
        return [_build_contact(c, p) for c, p in result.all()], total

    @staticmethod
    async def get_contact(db: AsyncSession, org_id: uuid.UUID, contact_id: uuid.UUID) -> ContactResponse:
        result = await db.execute(
            select(CrmContact, Person).join(Person, Person.id == CrmContact.person_id)
            .where(CrmContact.id == contact_id, CrmContact.organization_id == org_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Contact not found.")
        return _build_contact(row[0], row[1])

    @staticmethod
    async def update_contact(db: AsyncSession, org_id: uuid.UUID, contact_id: uuid.UUID, data: ContactUpdate) -> ContactResponse:
        result = await db.execute(
            select(CrmContact, Person).join(Person, Person.id == CrmContact.person_id)
            .where(CrmContact.id == contact_id, CrmContact.organization_id == org_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Contact not found.")
        contact, person = row
        update_data = data.model_dump(exclude_unset=True)
        person_updates = {k: v for k, v in update_data.items() if k in _PERSON_FIELDS}
        crm_updates = {k: v for k, v in update_data.items() if k in _CRM_FIELDS}
        if person_updates:
            person = await PeopleService.update_person(db, org_id, person.id, PersonUpdate(**person_updates))
        if crm_updates:
            for f, v in crm_updates.items():
                setattr(contact, f, v)
            await db.flush()
            await db.refresh(contact)
        return _build_contact(contact, person)


class CompanyService:

    @staticmethod
    async def list_companies(db: AsyncSession, org_id: uuid.UUID, search: str | None = None) -> list[CrmCompany]:
        q = select(CrmCompany).where(CrmCompany.organization_id == org_id)
        if search:
            q = q.where(CrmCompany.name.ilike(f"%{search}%"))
        q = q.order_by(CrmCompany.name)
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def create_company(db: AsyncSession, org_id: uuid.UUID, data: CompanyCreate) -> CrmCompany:
        company = CrmCompany(organization_id=org_id, **data.model_dump())
        db.add(company)
        await db.flush()
        await db.refresh(company)
        return company

    @staticmethod
    async def update_company(db: AsyncSession, org_id: uuid.UUID, company_id: uuid.UUID, data: CompanyUpdate) -> CrmCompany:
        result = await db.execute(select(CrmCompany).where(CrmCompany.id == company_id, CrmCompany.organization_id == org_id))
        company = result.scalar_one_or_none()
        if company is None:
            raise NotFoundError("Company not found.")
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(company, f, v)
        await db.flush()
        await db.refresh(company)
        return company
