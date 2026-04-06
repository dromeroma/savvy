"""FastAPI router for the SavvyPeople module."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.people.schemas import (
    EmergencyContactCreate,
    EmergencyContactResponse,
    FamilyRelationshipCreate,
    FamilyRelationshipResponse,
    PersonCreate,
    PersonListParams,
    PersonResponse,
    PersonStatsResponse,
    PersonUpdate,
)
from src.modules.people.service import PeopleService

router = APIRouter(prefix="/people", tags=["People"])


# ---------------------------------------------------------------------------
# People CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=dict,
    dependencies=[Depends(get_current_user)],
)
async def list_people(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    tags: list[str] | None = Query(None),
    scope_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List people with pagination, search, and filtering."""
    params = PersonListParams(
        status=status_filter,
        search=search,
        tags=tags,
        scope_id=scope_id,
        page=page,
        page_size=page_size,
    )
    people, total = await PeopleService.list_people(db, org_id, params)
    return {
        "data": [PersonResponse.model_validate(p) for p in people],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
    }


@router.post(
    "/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def create_person(
    data: PersonCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new person in the organization."""
    return await PeopleService.create_person(db, org_id, data)


@router.get(
    "/stats",
    response_model=PersonStatsResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Return aggregate statistics for people in the organization."""
    return await PeopleService.get_stats(db, org_id)


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Return a single person by ID."""
    return await PeopleService.get_person(db, org_id, person_id)


@router.patch(
    "/{person_id}",
    response_model=PersonResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_person(
    person_id: uuid.UUID,
    data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Partially update a person."""
    return await PeopleService.update_person(db, org_id, person_id, data)


@router.delete(
    "/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def delete_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Soft-delete a person."""
    await PeopleService.delete_person(db, org_id, person_id)


# ---------------------------------------------------------------------------
# Family Relationships
# ---------------------------------------------------------------------------


@router.get(
    "/{person_id}/family",
    response_model=list[FamilyRelationshipResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_family(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List family relationships for a person."""
    return await PeopleService.get_family(db, org_id, person_id)


@router.post(
    "/{person_id}/family",
    response_model=FamilyRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def add_family_relationship(
    person_id: uuid.UUID,
    data: FamilyRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Add a bidirectional family relationship."""
    rel = await PeopleService.add_family_relationship(db, org_id, person_id, data)
    # Fetch related person name for response
    from src.modules.people.models import Person
    from sqlalchemy import select

    related = await db.execute(select(Person).where(Person.id == rel.related_to))
    related_person = related.scalar_one()
    return FamilyRelationshipResponse(
        id=rel.id,
        person_id=rel.person_id,
        related_to=rel.related_to,
        related_person_name=f"{related_person.first_name} {related_person.last_name}",
        relationship=rel.relationship,
        created_at=rel.created_at,
    )


@router.delete(
    "/{person_id}/family/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def remove_family_relationship(
    person_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Remove a family relationship and its inverse."""
    await PeopleService.remove_family_relationship(db, org_id, relationship_id)


# ---------------------------------------------------------------------------
# Emergency Contacts
# ---------------------------------------------------------------------------


@router.get(
    "/{person_id}/emergency-contacts",
    response_model=list[EmergencyContactResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_emergency_contacts(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List emergency contacts for a person."""
    # Ensure person exists and belongs to org
    await PeopleService.get_person(db, org_id, person_id)
    return await PeopleService.get_emergency_contacts(db, person_id)


@router.post(
    "/{person_id}/emergency-contacts",
    response_model=EmergencyContactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def add_emergency_contact(
    person_id: uuid.UUID,
    data: EmergencyContactCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Add an emergency contact for a person."""
    await PeopleService.get_person(db, org_id, person_id)
    return await PeopleService.add_emergency_contact(db, person_id, data)


@router.delete(
    "/{person_id}/emergency-contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def remove_emergency_contact(
    person_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Remove an emergency contact."""
    await PeopleService.get_person(db, org_id, person_id)
    await PeopleService.remove_emergency_contact(db, contact_id)
