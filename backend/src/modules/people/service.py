"""Business logic for the SavvyPeople module."""

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.people.models import EmergencyContact, FamilyRelationship, Person
from src.modules.people.schemas import (
    EmergencyContactCreate,
    FamilyRelationshipCreate,
    FamilyRelationshipResponse,
    PersonCreate,
    PersonListParams,
    PersonStatsResponse,
    PersonUpdate,
)

# Map each relationship to its inverse counterpart.
INVERSE_RELATIONSHIPS: dict[str, str] = {
    "spouse": "spouse",
    "parent": "child",
    "child": "parent",
    "sibling": "sibling",
    "grandparent": "grandchild",
    "grandchild": "grandparent",
    "uncle_aunt": "nephew_niece",
    "nephew_niece": "uncle_aunt",
}


class PeopleService:
    """Stateless service layer for person management operations."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def list_people(
        db: AsyncSession,
        org_id: uuid.UUID,
        params: PersonListParams,
    ) -> tuple[list[Person], int]:
        """Return a paginated, filterable list of people."""
        base = select(Person).where(
            Person.organization_id == org_id,
            Person.deleted_at.is_(None),
        )

        # Filter by status
        if params.status:
            base = base.where(Person.status == params.status)

        # Filter by scope
        if params.scope_id:
            base = base.where(Person.scope_id == params.scope_id)

        # Full-text search across key fields
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

        # Filter by tags (JSONB contains)
        if params.tags:
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
            from sqlalchemy import cast

            base = base.where(
                Person.tags.op("@>")(cast(params.tags, PG_JSONB))
            )

        # Total count
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Pagination
        offset = (params.page - 1) * params.page_size
        rows_stmt = (
            base.order_by(Person.last_name, Person.first_name)
            .offset(offset)
            .limit(params.page_size)
        )
        result = await db.execute(rows_stmt)
        people = list(result.scalars().all())

        return people, total

    @staticmethod
    async def get_person(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
    ) -> Person:
        """Return a single person by ID within the organization."""
        result = await db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        person = result.scalar_one_or_none()
        if person is None:
            raise NotFoundError("Person not found.")
        return person

    @staticmethod
    async def create_person(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: PersonCreate,
    ) -> Person:
        """Create a new person record, validating email uniqueness per org."""
        if data.email:
            existing = await db.execute(
                select(Person).where(
                    Person.organization_id == org_id,
                    Person.email == data.email,
                    Person.deleted_at.is_(None),
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError(
                    "A person with this email already exists in the organization."
                )

        person = Person(
            organization_id=org_id,
            **data.model_dump(exclude_unset=True),
        )
        db.add(person)
        await db.flush()
        await db.refresh(person)
        return person

    @staticmethod
    async def update_person(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
        data: PersonUpdate,
    ) -> Person:
        """Apply partial updates to an existing person."""
        person = await PeopleService.get_person(db, org_id, person_id)

        update_data = data.model_dump(exclude_unset=True)

        # Validate email uniqueness if changing email
        new_email = update_data.get("email")
        if new_email and new_email != person.email:
            existing = await db.execute(
                select(Person).where(
                    Person.organization_id == org_id,
                    Person.email == new_email,
                    Person.deleted_at.is_(None),
                    Person.id != person_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError(
                    "A person with this email already exists in the organization."
                )

        for field, value in update_data.items():
            setattr(person, field, value)

        await db.flush()
        await db.refresh(person)
        return person

    @staticmethod
    async def delete_person(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
    ) -> None:
        """Soft-delete a person by setting deleted_at."""
        person = await PeopleService.get_person(db, org_id, person_id)
        person.deleted_at = func.now()
        person.status = "inactive"
        await db.flush()

    @staticmethod
    async def get_stats(
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> PersonStatsResponse:
        """Return aggregate statistics for people in the organization."""
        base_filter = and_(
            Person.organization_id == org_id,
            Person.deleted_at.is_(None),
        )

        # Total / active / inactive
        total_q = select(func.count()).where(base_filter)
        total = (await db.execute(total_q)).scalar_one()

        active_q = select(func.count()).where(base_filter, Person.status == "active")
        active = (await db.execute(active_q)).scalar_one()

        inactive = total - active

        # By gender
        gender_q = (
            select(
                func.coalesce(Person.gender, "unspecified").label("g"),
                func.count().label("c"),
            )
            .where(base_filter)
            .group_by("g")
        )
        gender_rows = (await db.execute(gender_q)).all()
        by_gender = {row.g: row.c for row in gender_rows}

        # By marital status
        marital_q = (
            select(
                func.coalesce(Person.marital_status, "unspecified").label("m"),
                func.count().label("c"),
            )
            .where(base_filter)
            .group_by("m")
        )
        marital_rows = (await db.execute(marital_q)).all()
        by_marital_status = {row.m: row.c for row in marital_rows}

        return PersonStatsResponse(
            total=total,
            active=active,
            inactive=inactive,
            by_gender=by_gender,
            by_marital_status=by_marital_status,
        )

    # ------------------------------------------------------------------
    # Family Relationships
    # ------------------------------------------------------------------

    @staticmethod
    async def get_family(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
    ) -> list[FamilyRelationshipResponse]:
        """Return all family relationships for a person with related person names."""
        # Alias for the related person
        RelatedPerson = Person

        stmt = (
            select(
                FamilyRelationship.id,
                FamilyRelationship.person_id,
                FamilyRelationship.related_to,
                FamilyRelationship.relationship,
                FamilyRelationship.created_at,
                func.concat(
                    RelatedPerson.first_name,
                    " ",
                    RelatedPerson.last_name,
                ).label("related_person_name"),
            )
            .join(RelatedPerson, RelatedPerson.id == FamilyRelationship.related_to)
            .where(
                FamilyRelationship.organization_id == org_id,
                FamilyRelationship.person_id == person_id,
            )
            .order_by(FamilyRelationship.relationship)
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            FamilyRelationshipResponse(
                id=row.id,
                person_id=row.person_id,
                related_to=row.related_to,
                related_person_name=row.related_person_name,
                relationship=row.relationship,
                created_at=row.created_at,
            )
            for row in rows
        ]

    @staticmethod
    async def add_family_relationship(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
        data: FamilyRelationshipCreate,
    ) -> FamilyRelationship:
        """Add a bidirectional family relationship between two people."""
        # Validate relationship type
        if data.relationship not in INVERSE_RELATIONSHIPS:
            raise ValidationError(
                f"Invalid relationship type '{data.relationship}'. "
                f"Allowed: {', '.join(INVERSE_RELATIONSHIPS.keys())}."
            )

        # Cannot relate to self
        if person_id == data.related_to:
            raise ValidationError("A person cannot have a family relationship with themselves.")

        # Verify related person exists in the same org
        related = await db.execute(
            select(Person).where(
                Person.id == data.related_to,
                Person.organization_id == org_id,
                Person.deleted_at.is_(None),
            )
        )
        if related.scalar_one_or_none() is None:
            raise NotFoundError("Related person not found in this organization.")

        # Check for duplicate
        existing = await db.execute(
            select(FamilyRelationship).where(
                FamilyRelationship.organization_id == org_id,
                FamilyRelationship.person_id == person_id,
                FamilyRelationship.related_to == data.related_to,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("This family relationship already exists.")

        # Spouse limit: max 1 active spouse per person
        if data.relationship == "spouse":
            spouse_count = await db.execute(
                select(func.count()).where(
                    FamilyRelationship.organization_id == org_id,
                    FamilyRelationship.person_id == person_id,
                    FamilyRelationship.relationship == "spouse",
                )
            )
            if spouse_count.scalar_one() > 0:
                raise ConflictError("This person already has a spouse relationship.")

            # Also check the related person's spouse count
            related_spouse_count = await db.execute(
                select(func.count()).where(
                    FamilyRelationship.organization_id == org_id,
                    FamilyRelationship.person_id == data.related_to,
                    FamilyRelationship.relationship == "spouse",
                )
            )
            if related_spouse_count.scalar_one() > 0:
                raise ConflictError("The related person already has a spouse relationship.")

        # Create forward relationship
        forward = FamilyRelationship(
            organization_id=org_id,
            person_id=person_id,
            related_to=data.related_to,
            relationship=data.relationship,
        )
        db.add(forward)

        # Create inverse relationship
        inverse = FamilyRelationship(
            organization_id=org_id,
            person_id=data.related_to,
            related_to=person_id,
            relationship=INVERSE_RELATIONSHIPS[data.relationship],
        )
        db.add(inverse)

        await db.flush()
        await db.refresh(forward)
        return forward

    @staticmethod
    async def remove_family_relationship(
        db: AsyncSession,
        org_id: uuid.UUID,
        relationship_id: uuid.UUID,
    ) -> None:
        """Remove a family relationship and its inverse."""
        result = await db.execute(
            select(FamilyRelationship).where(
                FamilyRelationship.id == relationship_id,
                FamilyRelationship.organization_id == org_id,
            )
        )
        rel = result.scalar_one_or_none()
        if rel is None:
            raise NotFoundError("Family relationship not found.")

        # Find and remove the inverse
        inverse_type = INVERSE_RELATIONSHIPS.get(rel.relationship, rel.relationship)
        inverse_result = await db.execute(
            select(FamilyRelationship).where(
                FamilyRelationship.organization_id == org_id,
                FamilyRelationship.person_id == rel.related_to,
                FamilyRelationship.related_to == rel.person_id,
                FamilyRelationship.relationship == inverse_type,
            )
        )
        inverse = inverse_result.scalar_one_or_none()
        if inverse is not None:
            await db.delete(inverse)

        await db.delete(rel)
        await db.flush()

    # ------------------------------------------------------------------
    # Emergency Contacts
    # ------------------------------------------------------------------

    @staticmethod
    async def get_emergency_contacts(
        db: AsyncSession,
        person_id: uuid.UUID,
    ) -> list[EmergencyContact]:
        """Return all emergency contacts for a person."""
        result = await db.execute(
            select(EmergencyContact)
            .where(EmergencyContact.person_id == person_id)
            .order_by(EmergencyContact.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_emergency_contact(
        db: AsyncSession,
        person_id: uuid.UUID,
        data: EmergencyContactCreate,
    ) -> EmergencyContact:
        """Add an emergency contact for a person."""
        contact = EmergencyContact(
            person_id=person_id,
            **data.model_dump(),
        )
        db.add(contact)
        await db.flush()
        await db.refresh(contact)
        return contact

    @staticmethod
    async def remove_emergency_contact(
        db: AsyncSession,
        contact_id: uuid.UUID,
    ) -> None:
        """Remove an emergency contact by ID."""
        result = await db.execute(
            select(EmergencyContact).where(EmergencyContact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        if contact is None:
            raise NotFoundError("Emergency contact not found.")
        await db.delete(contact)
        await db.flush()
