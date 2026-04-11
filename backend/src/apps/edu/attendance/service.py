"""Business logic for SavvyEdu attendance."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.edu.attendance.models import EduAttendance
from src.apps.edu.attendance.schemas import AttendanceSummary, BulkAttendanceCreate


class AttendanceService:
    """Attendance recording and summaries."""

    @staticmethod
    async def record_bulk(
        db: AsyncSession, org_id: uuid.UUID, data: BulkAttendanceCreate,
    ) -> list[EduAttendance]:
        results = []
        for record in data.records:
            # Upsert: check existing
            existing = await db.execute(
                select(EduAttendance).where(
                    EduAttendance.section_id == data.section_id,
                    EduAttendance.student_id == record.student_id,
                    EduAttendance.date == data.date,
                )
            )
            att = existing.scalar_one_or_none()
            if att:
                att.status = record.status
                att.notes = record.notes
            else:
                att = EduAttendance(
                    organization_id=org_id,
                    section_id=data.section_id,
                    student_id=record.student_id,
                    date=data.date,
                    status=record.status,
                    notes=record.notes,
                )
                db.add(att)
            results.append(att)

        await db.flush()
        for att in results:
            await db.refresh(att)
        return results

    @staticmethod
    async def list_by_section_date(
        db: AsyncSession, org_id: uuid.UUID,
        section_id: uuid.UUID, target_date: date,
    ) -> list[EduAttendance]:
        result = await db.execute(
            select(EduAttendance).where(
                EduAttendance.organization_id == org_id,
                EduAttendance.section_id == section_id,
                EduAttendance.date == target_date,
            ).order_by(EduAttendance.student_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_summary(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> AttendanceSummary:
        base = select(
            func.count().label("total"),
            func.count().filter(EduAttendance.status == "present").label("present"),
            func.count().filter(EduAttendance.status == "absent").label("absent"),
            func.count().filter(EduAttendance.status == "late").label("late"),
            func.count().filter(EduAttendance.status == "excused").label("excused"),
        ).where(
            EduAttendance.organization_id == org_id,
            EduAttendance.section_id == section_id,
        )
        result = await db.execute(base)
        row = result.one()
        total = row.total or 0
        present = row.present or 0
        late = row.late or 0

        sessions_result = await db.execute(
            select(func.count(func.distinct(EduAttendance.date))).where(
                EduAttendance.organization_id == org_id,
                EduAttendance.section_id == section_id,
            )
        )
        total_sessions = sessions_result.scalar() or 0

        return AttendanceSummary(
            section_id=section_id,
            total_sessions=total_sessions,
            present=present,
            absent=row.absent or 0,
            late=late,
            excused=row.excused or 0,
            attendance_rate=((present + late) / total * 100) if total > 0 else 0,
        )
