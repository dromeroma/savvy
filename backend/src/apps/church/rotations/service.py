"""Business logic for rotations sub-module."""

from __future__ import annotations

import uuid
from datetime import date as _date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.church.rotations.models import (
    ChurchRotation,
    ChurchRotationAssignment,
)
from src.apps.church.rotations.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    RotationCreate,
    RotationUpdate,
)


class RotationService:

    @staticmethod
    async def list_rotations(
        db: AsyncSession, org_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[ChurchRotation]:
        stmt = (
            select(ChurchRotation)
            .where(ChurchRotation.organization_id == org_id)
            .order_by(ChurchRotation.name)
        )
        if active_only:
            stmt = stmt.where(ChurchRotation.active.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_rotation(
        db: AsyncSession, org_id: uuid.UUID, rotation_id: uuid.UUID,
    ) -> ChurchRotation:
        rot = await db.get(ChurchRotation, rotation_id)
        if rot is None or rot.organization_id != org_id:
            raise NotFoundError("Rotation not found.")
        return rot

    @staticmethod
    async def create_rotation(
        db: AsyncSession, org_id: uuid.UUID, data: RotationCreate,
    ) -> ChurchRotation:
        rot = ChurchRotation(organization_id=org_id, **data.model_dump())
        db.add(rot)
        await db.flush()
        await db.refresh(rot)
        return rot

    @staticmethod
    async def update_rotation(
        db: AsyncSession, org_id: uuid.UUID,
        rotation_id: uuid.UUID, data: RotationUpdate,
    ) -> ChurchRotation:
        rot = await RotationService.get_rotation(db, org_id, rotation_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rot, field, value)
        await db.flush()
        await db.refresh(rot)
        return rot


class AssignmentService:

    @staticmethod
    async def list_assignments(
        db: AsyncSession, org_id: uuid.UUID,
        rotation_id: uuid.UUID | None = None,
        person_id: uuid.UUID | None = None,
        from_date: _date | None = None,
        to_date: _date | None = None,
    ) -> list[ChurchRotationAssignment]:
        stmt = (
            select(ChurchRotationAssignment)
            .where(ChurchRotationAssignment.organization_id == org_id)
            .order_by(ChurchRotationAssignment.assignment_date.desc())
        )
        if rotation_id:
            stmt = stmt.where(ChurchRotationAssignment.rotation_id == rotation_id)
        if person_id:
            stmt = stmt.where(ChurchRotationAssignment.person_id == person_id)
        if from_date:
            stmt = stmt.where(ChurchRotationAssignment.assignment_date >= from_date)
        if to_date:
            stmt = stmt.where(ChurchRotationAssignment.assignment_date <= to_date)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_assignment(
        db: AsyncSession, org_id: uuid.UUID, data: AssignmentCreate,
    ) -> ChurchRotationAssignment:
        assignment = ChurchRotationAssignment(
            organization_id=org_id, **data.model_dump(),
        )
        db.add(assignment)
        await db.flush()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def update_assignment(
        db: AsyncSession, org_id: uuid.UUID,
        assignment_id: uuid.UUID, data: AssignmentUpdate,
    ) -> ChurchRotationAssignment:
        assignment = await db.get(ChurchRotationAssignment, assignment_id)
        if assignment is None or assignment.organization_id != org_id:
            raise NotFoundError("Assignment not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(assignment, field, value)
        await db.flush()
        await db.refresh(assignment)
        return assignment
