"""Business logic for doctrine sub-module."""

from __future__ import annotations

import uuid
from datetime import date as _date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.church.doctrine.models import (
    ChurchDoctrineAttendance,
    ChurchDoctrineEnrollment,
    ChurchDoctrineGroup,
)
from src.apps.church.doctrine.schemas import (
    DoctrineAttendanceBulkCreate,
    DoctrineAttendanceCreate,
    DoctrineGroupCreate,
    DoctrineGroupUpdate,
    EnrollmentCreate,
    EnrollmentUpdate,
)


# ------------------------------------------------------------------
# Groups
# ------------------------------------------------------------------

class DoctrineGroupService:

    @staticmethod
    async def list_groups(
        db: AsyncSession, org_id: uuid.UUID,
        status: str | None = None,
        scope_id: uuid.UUID | None = None,
    ) -> list[ChurchDoctrineGroup]:
        stmt = select(ChurchDoctrineGroup).where(
            ChurchDoctrineGroup.organization_id == org_id,
        ).order_by(ChurchDoctrineGroup.start_date.desc().nullslast())
        if status:
            stmt = stmt.where(ChurchDoctrineGroup.status == status)
        if scope_id:
            stmt = stmt.where(ChurchDoctrineGroup.scope_id == scope_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_group(
        db: AsyncSession, org_id: uuid.UUID, group_id: uuid.UUID,
    ) -> ChurchDoctrineGroup:
        group = await db.get(ChurchDoctrineGroup, group_id)
        if group is None or group.organization_id != org_id:
            raise NotFoundError("Doctrine group not found.")
        return group

    @staticmethod
    async def create_group(
        db: AsyncSession, org_id: uuid.UUID, data: DoctrineGroupCreate,
    ) -> ChurchDoctrineGroup:
        group = ChurchDoctrineGroup(organization_id=org_id, **data.model_dump())
        db.add(group)
        await db.flush()
        await db.refresh(group)
        return group

    @staticmethod
    async def update_group(
        db: AsyncSession, org_id: uuid.UUID,
        group_id: uuid.UUID, data: DoctrineGroupUpdate,
    ) -> ChurchDoctrineGroup:
        group = await DoctrineGroupService.get_group(db, org_id, group_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(group, field, value)
        await db.flush()
        await db.refresh(group)
        return group


# ------------------------------------------------------------------
# Enrollments
# ------------------------------------------------------------------

class EnrollmentService:

    @staticmethod
    async def list_enrollments(
        db: AsyncSession, org_id: uuid.UUID, group_id: uuid.UUID,
    ) -> list[ChurchDoctrineEnrollment]:
        result = await db.execute(
            select(ChurchDoctrineEnrollment)
            .where(
                ChurchDoctrineEnrollment.organization_id == org_id,
                ChurchDoctrineEnrollment.doctrine_group_id == group_id,
            )
            .order_by(ChurchDoctrineEnrollment.enrolled_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_enrollment(
        db: AsyncSession, org_id: uuid.UUID, data: EnrollmentCreate,
    ) -> ChurchDoctrineEnrollment:
        payload = data.model_dump()
        if payload.get("enrolled_at") is None:
            payload["enrolled_at"] = _date.today()
        enrollment = ChurchDoctrineEnrollment(
            organization_id=org_id,
            **payload,
        )
        db.add(enrollment)
        await db.flush()
        await db.refresh(enrollment)
        return enrollment

    @staticmethod
    async def update_enrollment(
        db: AsyncSession, org_id: uuid.UUID,
        enrollment_id: uuid.UUID, data: EnrollmentUpdate,
    ) -> ChurchDoctrineEnrollment:
        enrollment = await db.get(ChurchDoctrineEnrollment, enrollment_id)
        if enrollment is None or enrollment.organization_id != org_id:
            raise NotFoundError("Enrollment not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(enrollment, field, value)
        await db.flush()
        await db.refresh(enrollment)
        return enrollment


# ------------------------------------------------------------------
# Attendance
# ------------------------------------------------------------------

class DoctrineAttendanceService:

    @staticmethod
    async def list_attendance(
        db: AsyncSession, org_id: uuid.UUID,
        group_id: uuid.UUID, session_date: _date | None = None,
    ) -> list[ChurchDoctrineAttendance]:
        stmt = (
            select(ChurchDoctrineAttendance)
            .where(
                ChurchDoctrineAttendance.organization_id == org_id,
                ChurchDoctrineAttendance.doctrine_group_id == group_id,
            )
            .order_by(ChurchDoctrineAttendance.session_date.desc())
        )
        if session_date:
            stmt = stmt.where(ChurchDoctrineAttendance.session_date == session_date)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_attendance(
        db: AsyncSession, org_id: uuid.UUID, data: DoctrineAttendanceCreate,
    ) -> ChurchDoctrineAttendance:
        row = ChurchDoctrineAttendance(organization_id=org_id, **data.model_dump())
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return row

    @staticmethod
    async def bulk_create(
        db: AsyncSession, org_id: uuid.UUID, data: DoctrineAttendanceBulkCreate,
    ) -> list[ChurchDoctrineAttendance]:
        rows: list[ChurchDoctrineAttendance] = []
        for entry in data.entries:
            rows.append(
                ChurchDoctrineAttendance(
                    organization_id=org_id,
                    doctrine_group_id=data.doctrine_group_id,
                    person_id=entry["person_id"],
                    session_date=data.session_date,
                    present=entry.get("present", True),
                )
            )
        db.add_all(rows)
        await db.flush()
        for r in rows:
            await db.refresh(r)
        return rows
