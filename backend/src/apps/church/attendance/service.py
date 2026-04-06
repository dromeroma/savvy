"""Business logic for church attendance."""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.attendance.models import ChurchAttendance
from src.apps.church.attendance.schemas import AttendanceBulkCreate, AttendanceSummary
from src.apps.church.events.models import ChurchEvent


class AttendanceService:

    @staticmethod
    async def record_attendance(
        db: AsyncSession, org_id: uuid.UUID, data: AttendanceBulkCreate,
    ) -> int:
        """Bulk upsert attendance for an event. Returns count of records."""
        # Remove existing records for this event
        await db.execute(
            delete(ChurchAttendance).where(
                ChurchAttendance.organization_id == org_id,
                ChurchAttendance.event_id == data.event_id,
            )
        )
        count = 0
        for record in data.records:
            att = ChurchAttendance(
                organization_id=org_id,
                event_id=data.event_id,
                person_id=record.person_id,
                status=record.status,
            )
            db.add(att)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def get_event_attendance(
        db: AsyncSession, org_id: uuid.UUID, event_id: uuid.UUID,
    ) -> list[ChurchAttendance]:
        result = await db.execute(
            select(ChurchAttendance).where(
                ChurchAttendance.organization_id == org_id,
                ChurchAttendance.event_id == event_id,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_summary(
        db: AsyncSession, org_id: uuid.UUID, limit: int = 20,
    ) -> list[AttendanceSummary]:
        """Get attendance summary per event."""
        stmt = (
            select(
                ChurchAttendance.event_id,
                ChurchEvent.name,
                ChurchEvent.date,
                func.count(ChurchAttendance.id).label("total"),
                func.count().filter(ChurchAttendance.status == "present").label("present"),
                func.count().filter(ChurchAttendance.status == "absent").label("absent"),
                func.count().filter(ChurchAttendance.status == "late").label("late"),
            )
            .join(ChurchEvent, ChurchEvent.id == ChurchAttendance.event_id)
            .where(ChurchAttendance.organization_id == org_id)
            .group_by(ChurchAttendance.event_id, ChurchEvent.name, ChurchEvent.date)
            .order_by(ChurchEvent.date.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [
            AttendanceSummary(
                event_id=str(row.event_id),
                event_name=row.name,
                event_date=str(row.date),
                total=row.total,
                present=row.present,
                absent=row.absent,
                late=row.late,
            )
            for row in result.all()
        ]
