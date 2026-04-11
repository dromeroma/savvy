"""Business logic for SavvyEdu scheduling."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.apps.edu.scheduling.models import EduRoom, EduSchedule
from src.apps.edu.scheduling.schemas import RoomCreate, RoomUpdate, ScheduleCreate


class SchedulingService:
    """Rooms and schedule management with conflict detection."""

    # ------------------------------------------------------------------
    # Rooms
    # ------------------------------------------------------------------

    @staticmethod
    async def list_rooms(db: AsyncSession, org_id: uuid.UUID) -> list[EduRoom]:
        result = await db.execute(
            select(EduRoom).where(EduRoom.organization_id == org_id).order_by(EduRoom.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_room(db: AsyncSession, org_id: uuid.UUID, data: RoomCreate) -> EduRoom:
        room = EduRoom(
            organization_id=org_id,
            scope_id=data.scope_id,
            name=data.name,
            building=data.building,
            floor=data.floor,
            capacity=data.capacity,
            type=data.type,
            equipment=data.equipment,
        )
        db.add(room)
        await db.flush()
        await db.refresh(room)
        return room

    @staticmethod
    async def update_room(
        db: AsyncSession, org_id: uuid.UUID, room_id: uuid.UUID, data: RoomUpdate,
    ) -> EduRoom:
        result = await db.execute(
            select(EduRoom).where(EduRoom.id == room_id, EduRoom.organization_id == org_id)
        )
        room = result.scalar_one_or_none()
        if room is None:
            raise NotFoundError("Room not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(room, field, value)
        await db.flush()
        await db.refresh(room)
        return room

    # ------------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------------

    @staticmethod
    async def list_schedules(
        db: AsyncSession, section_id: uuid.UUID | None = None,
    ) -> list[EduSchedule]:
        q = select(EduSchedule)
        if section_id:
            q = q.where(EduSchedule.section_id == section_id)
        q = q.order_by(EduSchedule.day_of_week, EduSchedule.start_time)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_schedule(db: AsyncSession, org_id: uuid.UUID, data: ScheduleCreate) -> EduSchedule:
        if data.end_time <= data.start_time:
            raise ValidationError("End time must be after start time.")

        # Conflict detection: room overlap
        if data.room_id:
            conflicts = await db.execute(
                select(EduSchedule).where(
                    EduSchedule.room_id == data.room_id,
                    EduSchedule.day_of_week == data.day_of_week,
                    EduSchedule.start_time < data.end_time,
                    EduSchedule.end_time > data.start_time,
                )
            )
            if conflicts.scalar_one_or_none():
                raise ConflictError("Room conflict: another section uses this room at the same time.")

        # Conflict detection: teacher overlap (via section's teacher)
        from src.apps.edu.enrollment.models import EduSection
        section = await db.execute(
            select(EduSection).where(EduSection.id == data.section_id)
        )
        section_row = section.scalar_one_or_none()
        if section_row and section_row.teacher_id:
            teacher_sections = await db.execute(
                select(EduSection.id).where(
                    EduSection.teacher_id == section_row.teacher_id,
                    EduSection.id != data.section_id,
                )
            )
            other_section_ids = [r[0] for r in teacher_sections.all()]
            if other_section_ids:
                teacher_conflicts = await db.execute(
                    select(EduSchedule).where(
                        EduSchedule.section_id.in_(other_section_ids),
                        EduSchedule.day_of_week == data.day_of_week,
                        EduSchedule.start_time < data.end_time,
                        EduSchedule.end_time > data.start_time,
                    )
                )
                if teacher_conflicts.scalar_one_or_none():
                    raise ConflictError("Teacher conflict: the teacher has another section at the same time.")

        schedule = EduSchedule(
            section_id=data.section_id,
            room_id=data.room_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        db.add(schedule)
        await db.flush()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def delete_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> None:
        result = await db.execute(
            select(EduSchedule).where(EduSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule is None:
            raise NotFoundError("Schedule not found.")
        await db.delete(schedule)
        await db.flush()
