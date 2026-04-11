"""Business logic for SavvyFamily — family units, members, relationships, annotations, genogram data."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.apps.family.models import (
    FamilyAnnotation,
    FamilyMember,
    FamilyRelationshipMeta,
    FamilyUnit,
)
from src.apps.family.schemas import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyUnitCreate,
    FamilyUnitUpdate,
    GenogramData,
    GenogramEdge,
    GenogramNode,
    FamilyUnitResponse,
    RelationshipMetaCreate,
)
from src.modules.people.models import FamilyRelationship, Person


class FamilyService:
    """CRUD for family units, members, relationships, annotations, and genogram assembly."""

    # ------------------------------------------------------------------
    # Family Units
    # ------------------------------------------------------------------

    @staticmethod
    async def list_units(
        db: AsyncSession, org_id: uuid.UUID,
        search: str | None = None,
    ) -> list[FamilyUnit]:
        q = select(FamilyUnit).where(FamilyUnit.organization_id == org_id)
        if search:
            q = q.where(FamilyUnit.name.ilike(f"%{search}%"))
        q = q.order_by(FamilyUnit.name)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_unit(
        db: AsyncSession, org_id: uuid.UUID, data: FamilyUnitCreate,
    ) -> FamilyUnit:
        unit = FamilyUnit(
            organization_id=org_id,
            name=data.name,
            type=data.type,
            address=data.address,
            city=data.city,
            phone=data.phone,
            notes=data.notes,
        )
        db.add(unit)
        await db.flush()
        await db.refresh(unit)
        return unit

    @staticmethod
    async def get_unit(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID,
    ) -> FamilyUnit:
        result = await db.execute(
            select(FamilyUnit).where(
                FamilyUnit.id == unit_id,
                FamilyUnit.organization_id == org_id,
            )
        )
        unit = result.scalar_one_or_none()
        if unit is None:
            raise NotFoundError("Family unit not found.")
        return unit

    @staticmethod
    async def update_unit(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID, data: FamilyUnitUpdate,
    ) -> FamilyUnit:
        unit = await FamilyService.get_unit(db, org_id, unit_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(unit, field, value)
        await db.flush()
        await db.refresh(unit)
        return unit

    @staticmethod
    async def get_unit_member_count(
        db: AsyncSession, unit_id: uuid.UUID,
    ) -> int:
        result = await db.execute(
            select(func.count()).where(FamilyMember.family_unit_id == unit_id)
        )
        return result.scalar() or 0

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    @staticmethod
    async def list_members(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID,
    ) -> list[FamilyMemberResponse]:
        result = await db.execute(
            select(FamilyMember, Person)
            .join(Person, Person.id == FamilyMember.person_id)
            .where(
                FamilyMember.family_unit_id == unit_id,
                FamilyMember.organization_id == org_id,
            )
            .order_by(FamilyMember.generation, Person.date_of_birth)
        )
        items = []
        for member, person in result.all():
            items.append(FamilyMemberResponse(
                id=member.id,
                family_unit_id=member.family_unit_id,
                person_id=member.person_id,
                role=member.role,
                is_deceased=member.is_deceased,
                death_date=member.death_date,
                generation=member.generation,
                position_x=member.position_x,
                position_y=member.position_y,
                created_at=member.created_at,
                first_name=person.first_name,
                last_name=person.last_name,
                gender=person.gender,
                date_of_birth=person.date_of_birth,
                photo_url=person.photo_url,
                marital_status=person.marital_status,
            ))
        return items

    @staticmethod
    async def add_member(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID, data: FamilyMemberCreate,
    ) -> FamilyMember:
        member = FamilyMember(
            organization_id=org_id,
            family_unit_id=unit_id,
            person_id=data.person_id,
            role=data.role,
            is_deceased=data.is_deceased,
            death_date=data.death_date,
            generation=data.generation,
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member(
        db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID, data: FamilyMemberUpdate,
    ) -> FamilyMember:
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.id == member_id,
                FamilyMember.organization_id == org_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError("Family member not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID,
    ) -> None:
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.id == member_id,
                FamilyMember.organization_id == org_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError("Family member not found.")
        await db.delete(member)
        await db.flush()

    # ------------------------------------------------------------------
    # Relationship Metadata
    # ------------------------------------------------------------------

    @staticmethod
    async def add_relationship_meta(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID, data: RelationshipMetaCreate,
    ) -> FamilyRelationshipMeta:
        meta = FamilyRelationshipMeta(
            family_unit_id=unit_id,
            person_id=data.person_id,
            related_to_id=data.related_to_id,
            relationship_type=data.relationship_type,
            start_date=data.start_date,
            end_date=data.end_date,
            notes=data.notes,
        )
        db.add(meta)
        await db.flush()
        await db.refresh(meta)
        return meta

    @staticmethod
    async def list_relationship_meta(
        db: AsyncSession, unit_id: uuid.UUID,
    ) -> list[FamilyRelationshipMeta]:
        result = await db.execute(
            select(FamilyRelationshipMeta)
            .where(FamilyRelationshipMeta.family_unit_id == unit_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------

    @staticmethod
    async def list_annotations(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID,
        person_id: uuid.UUID | None = None,
    ) -> list[FamilyAnnotation]:
        q = select(FamilyAnnotation).where(
            FamilyAnnotation.organization_id == org_id,
            FamilyAnnotation.family_unit_id == unit_id,
        )
        if person_id:
            q = q.where(FamilyAnnotation.person_id == person_id)
        q = q.order_by(FamilyAnnotation.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_annotation(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID, data: AnnotationCreate,
    ) -> FamilyAnnotation:
        ann = FamilyAnnotation(
            organization_id=org_id,
            family_unit_id=unit_id,
            person_id=data.person_id,
            category=data.category,
            severity=data.severity,
            description=data.description,
            diagnosed_date=data.diagnosed_date,
            source_app=data.source_app,
        )
        db.add(ann)
        await db.flush()
        await db.refresh(ann)
        return ann

    @staticmethod
    async def update_annotation(
        db: AsyncSession, org_id: uuid.UUID, ann_id: uuid.UUID, data: AnnotationUpdate,
    ) -> FamilyAnnotation:
        result = await db.execute(
            select(FamilyAnnotation).where(
                FamilyAnnotation.id == ann_id,
                FamilyAnnotation.organization_id == org_id,
            )
        )
        ann = result.scalar_one_or_none()
        if ann is None:
            raise NotFoundError("Annotation not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ann, field, value)
        await db.flush()
        await db.refresh(ann)
        return ann

    # ------------------------------------------------------------------
    # Genogram Assembly
    # ------------------------------------------------------------------

    @staticmethod
    async def get_genogram(
        db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID,
    ) -> GenogramData:
        """Assemble complete genogram data for a family unit."""
        unit = await FamilyService.get_unit(db, org_id, unit_id)
        members = await FamilyService.list_members(db, org_id, unit_id)
        rel_metas = await FamilyService.list_relationship_meta(db, unit_id)
        annotations = await FamilyService.list_annotations(db, org_id, unit_id)

        # Build nodes
        nodes: list[GenogramNode] = []
        for m in members:
            person_annotations = [
                AnnotationResponse.model_validate(a)
                for a in annotations if a.person_id == m.person_id
            ]
            nodes.append(GenogramNode(
                id=m.id,
                person_id=m.person_id,
                first_name=m.first_name or "",
                last_name=m.last_name or "",
                gender=m.gender,
                date_of_birth=m.date_of_birth,
                is_deceased=m.is_deceased,
                death_date=m.death_date,
                role=m.role,
                generation=m.generation,
                position_x=m.position_x,
                position_y=m.position_y,
                annotations=person_annotations,
            ))

        # Build edges from relationship metadata (marriages, etc.)
        edges: list[GenogramEdge] = []
        for rm in rel_metas:
            edges.append(GenogramEdge(
                source_person_id=rm.person_id,
                target_person_id=rm.related_to_id,
                relationship_type=rm.relationship_type,
                status=rm.status,
            ))

        # Also add parent-child edges from the shared family_relationships table
        member_person_ids = [m.person_id for m in members]
        if member_person_ids:
            fr_result = await db.execute(
                select(FamilyRelationship).where(
                    FamilyRelationship.organization_id == org_id,
                    FamilyRelationship.person_id.in_(member_person_ids),
                    FamilyRelationship.related_to.in_(member_person_ids),
                )
            )
            for fr in fr_result.scalars().all():
                # Avoid duplicating edges already in relationship_meta
                already_exists = any(
                    e.source_person_id == fr.person_id and e.target_person_id == fr.related_to
                    for e in edges
                )
                if not already_exists:
                    edges.append(GenogramEdge(
                        source_person_id=fr.person_id,
                        target_person_id=fr.related_to,
                        relationship_type=fr.relationship,
                        status="active",
                    ))

        return GenogramData(
            family_unit=FamilyUnitResponse.model_validate(unit),
            nodes=nodes,
            edges=edges,
        )
