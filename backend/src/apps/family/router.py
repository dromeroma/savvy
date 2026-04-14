"""SavvyFamily REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.family.schemas import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyUnitCreate,
    FamilyUnitResponse,
    FamilyUnitUpdate,
    GenogramData,
    RelationshipMetaCreate,
    RelationshipMetaResponse,
)
from src.apps.family.service import FamilyService

router = APIRouter(
    prefix="/family",
    tags=["SavvyFamily"],
    dependencies=[Depends(require_permission("family", "families.write", "families.read"))],
)


# ---------------------------------------------------------------------------
# Family Units
# ---------------------------------------------------------------------------


@router.get("/units", response_model=list[FamilyUnitResponse])
async def list_units(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.list_units(db, org_id, search)


@router.post("/units", response_model=FamilyUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    data: FamilyUnitCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.create_unit(db, org_id, data)


@router.get("/units/{unit_id}", response_model=FamilyUnitResponse)
async def get_unit(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.get_unit(db, org_id, unit_id)


@router.patch("/units/{unit_id}", response_model=FamilyUnitResponse)
async def update_unit(
    unit_id: uuid.UUID,
    data: FamilyUnitUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.update_unit(db, org_id, unit_id, data)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@router.get("/units/{unit_id}/members", response_model=list[FamilyMemberResponse])
async def list_members(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.list_members(db, org_id, unit_id)


@router.post("/units/{unit_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    unit_id: uuid.UUID,
    data: FamilyMemberCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    member = await FamilyService.add_member(db, org_id, unit_id, data)
    return {"id": str(member.id), "person_id": str(member.person_id), "role": member.role}


@router.patch("/members/{member_id}")
async def update_member(
    member_id: uuid.UUID,
    data: FamilyMemberUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    member = await FamilyService.update_member(db, org_id, member_id, data)
    return {"id": str(member.id), "role": member.role, "generation": member.generation}


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await FamilyService.remove_member(db, org_id, member_id)


# ---------------------------------------------------------------------------
# Relationship Metadata
# ---------------------------------------------------------------------------


@router.get("/units/{unit_id}/relationships", response_model=list[RelationshipMetaResponse])
async def list_relationships(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.list_relationship_meta(db, unit_id)


@router.post("/units/{unit_id}/relationships", response_model=RelationshipMetaResponse, status_code=status.HTTP_201_CREATED)
async def add_relationship(
    unit_id: uuid.UUID,
    data: RelationshipMetaCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.add_relationship_meta(db, org_id, unit_id, data)


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------


@router.get("/units/{unit_id}/annotations", response_model=list[AnnotationResponse])
async def list_annotations(
    unit_id: uuid.UUID,
    person_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.list_annotations(db, org_id, unit_id, person_id)


@router.post("/units/{unit_id}/annotations", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    unit_id: uuid.UUID,
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.create_annotation(db, org_id, unit_id, data)


@router.patch("/annotations/{ann_id}", response_model=AnnotationResponse)
async def update_annotation(
    ann_id: uuid.UUID,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.update_annotation(db, org_id, ann_id, data)


# ---------------------------------------------------------------------------
# Genogram
# ---------------------------------------------------------------------------


@router.get("/units/{unit_id}/genogram", response_model=GenogramData)
async def get_genogram(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FamilyService.get_genogram(db, org_id, unit_id)
