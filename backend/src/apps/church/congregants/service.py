"""Business logic for church congregant management.

Delegates person-level operations to PeopleService and manages the
church_congregants table for ecclesiastical data.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.apps.church.congregants.models import ChurchCongregant
from src.apps.church.congregants.schemas import (
    CongregantCreate,
    CongregantListParams,
    CongregantResponse,
    CongregantUpdate,
)
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate, PersonUpdate
from src.modules.people.service import PeopleService

# Fields that belong to the Person model (forwarded to PeopleService).
_PERSON_FIELDS = {
    "first_name", "last_name", "email", "phone", "date_of_birth",
    "gender", "document_type", "document_number", "occupation", "status",
    "country", "state", "city", "address", "mobile", "second_last_name",
    "marital_status",
}

# Fields that belong to the ChurchCongregant model.
_CHURCH_FIELDS = {
    "scope_id", "membership_date", "baptism_date", "holy_spirit_baptism",
    "conversion_date", "spiritual_status", "referred_by", "pastoral_notes",
}


def _build_response(congregant: ChurchCongregant, person: Person) -> CongregantResponse:
    """Combine a Person row and a ChurchCongregant row into one response."""
    return CongregantResponse(
        id=congregant.id,
        organization_id=congregant.organization_id,
        person_id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        email=person.email,
        phone=person.phone,
        date_of_birth=person.date_of_birth,
        gender=person.gender,
        document_type=person.document_type,
        document_number=person.document_number,
        occupation=person.occupation,
        country=person.country,
        state=person.state,
        city=person.city,
        address=person.address,
        photo_url=person.photo_url,
        status=person.status,
        scope_id=congregant.scope_id,
        membership_date=congregant.membership_date,
        baptism_date=congregant.baptism_date,
        holy_spirit_baptism=congregant.holy_spirit_baptism,
        conversion_date=congregant.conversion_date,
        spiritual_status=congregant.spiritual_status,
        referred_by=congregant.referred_by,
        pastoral_notes=congregant.pastoral_notes,
        inactivation_reason=congregant.inactivation_reason,
        inactivated_at=congregant.inactivated_at,
        created_at=congregant.created_at,
        updated_at=congregant.updated_at,
    )


class CongregantService:
    """CRUD operations for church congregants backed by SavvyPeople."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_congregant(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: CongregantCreate,
    ) -> CongregantResponse:
        """Create a person via PeopleService, then attach a congregant record."""
        # 1. Build person payload from the incoming data
        person_data = PersonCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            document_type=data.document_type,
            document_number=data.document_number,
        )
        person = await PeopleService.create_person(db, org_id, person_data)

        # 2. Create church congregant record linked to the person
        congregant = ChurchCongregant(
            organization_id=org_id,
            person_id=person.id,
            scope_id=data.scope_id,
            membership_date=data.membership_date,
            baptism_date=data.baptism_date,
            conversion_date=data.conversion_date,
            spiritual_status=data.spiritual_status,
            referred_by=data.referred_by,
            pastoral_notes=data.pastoral_notes,
        )
        db.add(congregant)
        await db.flush()
        await db.refresh(congregant)

        return _build_response(congregant, person)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @staticmethod
    async def list_congregants(
        db: AsyncSession,
        org_id: uuid.UUID,
        params: CongregantListParams,
    ) -> tuple[list[CongregantResponse], int]:
        """List congregants with search, filters, and pagination.

        Joins people + church_congregants so callers get a flat view.
        """
        base = (
            select(ChurchCongregant, Person)
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )

        # Filters
        if params.status:
            base = base.where(Person.status == params.status)

        if params.spiritual_status:
            base = base.where(ChurchCongregant.spiritual_status == params.spiritual_status)

        if params.scope_id:
            base = base.where(ChurchCongregant.scope_id == params.scope_id)

        if params.search:
            term = f"%{params.search}%"
            base = base.where(
                or_(
                    Person.first_name.ilike(term),
                    Person.last_name.ilike(term),
                    Person.email.ilike(term),
                    Person.phone.ilike(term),
                    Person.document_number.ilike(term),
                )
            )

        # Total count
        count_result = await db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar() or 0

        # Paginated results
        offset = (params.page - 1) * params.page_size
        result = await db.execute(
            base.order_by(Person.last_name, Person.first_name)
            .offset(offset)
            .limit(params.page_size)
        )
        rows = result.all()

        items = [_build_response(congregant, person) for congregant, person in rows]
        return items, total

    # ------------------------------------------------------------------
    # Get
    # ------------------------------------------------------------------

    @staticmethod
    async def get_congregant(
        db: AsyncSession,
        org_id: uuid.UUID,
        congregant_id: uuid.UUID,
    ) -> CongregantResponse:
        """Get a single congregant by congregant ID."""
        result = await db.execute(
            select(ChurchCongregant, Person)
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.id == congregant_id,
                ChurchCongregant.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Congregant not found.")

        congregant, person = row
        return _build_response(congregant, person)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_congregant(
        db: AsyncSession,
        org_id: uuid.UUID,
        congregant_id: uuid.UUID,
        data: CongregantUpdate,
    ) -> CongregantResponse:
        """Update person fields via PeopleService and church fields directly."""
        # Fetch the congregant + person
        result = await db.execute(
            select(ChurchCongregant, Person)
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.id == congregant_id,
                ChurchCongregant.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Congregant not found.")

        congregant, person = row
        update_data = data.model_dump(exclude_unset=True)

        # Split into person vs church fields
        person_updates = {k: v for k, v in update_data.items() if k in _PERSON_FIELDS}
        church_updates = {k: v for k, v in update_data.items() if k in _CHURCH_FIELDS}

        # Update person fields via PeopleService
        if person_updates:
            person_update = PersonUpdate(**person_updates)
            person = await PeopleService.update_person(db, org_id, person.id, person_update)

        # Update church fields directly
        if church_updates:
            for field, value in church_updates.items():
                setattr(congregant, field, value)
            await db.flush()
            await db.refresh(congregant)

        return _build_response(congregant, person)

    # ------------------------------------------------------------------
    # Inactivate / Reactivate
    # ------------------------------------------------------------------

    @staticmethod
    async def inactivate_congregant(
        db: AsyncSession,
        org_id: uuid.UUID,
        congregant_id: uuid.UUID,
        reason: str,
    ) -> CongregantResponse:
        """Inactivate a congregant with a reason."""
        from datetime import UTC, datetime as dt

        result = await db.execute(
            select(ChurchCongregant, Person)
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.id == congregant_id,
                ChurchCongregant.organization_id == org_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Congregant not found.")

        congregant, person = row
        person.status = "inactive"
        congregant.inactivation_reason = reason
        congregant.inactivated_at = dt.now(UTC)
        await db.flush()
        await db.refresh(congregant)
        await db.refresh(person)
        return _build_response(congregant, person)

    @staticmethod
    async def reactivate_congregant(
        db: AsyncSession,
        org_id: uuid.UUID,
        congregant_id: uuid.UUID,
    ) -> CongregantResponse:
        """Reactivate an inactive congregant."""
        result = await db.execute(
            select(ChurchCongregant, Person)
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.id == congregant_id,
                ChurchCongregant.organization_id == org_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Congregant not found.")

        congregant, person = row
        person.status = "active"
        congregant.inactivation_reason = None
        congregant.inactivated_at = None
        await db.flush()
        await db.refresh(congregant)
        await db.refresh(person)
        return _build_response(congregant, person)
