"""Business logic for SavvyEdu enrollment — sections, enrollments, waitlists."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.apps.edu.enrollment.models import EduEnrollment, EduSection, EduWaitlist
from src.apps.edu.enrollment.schemas import (
    EnrollmentCreate,
    EnrollmentUpdate,
    SectionCreate,
    SectionUpdate,
)


class EnrollmentService:
    """Sections, enrollments, and waitlists."""

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    @staticmethod
    async def list_sections(
        db: AsyncSession, org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
        course_id: uuid.UUID | None = None,
    ) -> list[EduSection]:
        q = select(EduSection).where(EduSection.organization_id == org_id)
        if period_id:
            q = q.where(EduSection.academic_period_id == period_id)
        if course_id:
            q = q.where(EduSection.course_id == course_id)
        q = q.order_by(EduSection.code)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_section(
        db: AsyncSession, org_id: uuid.UUID, data: SectionCreate,
    ) -> EduSection:
        section = EduSection(
            organization_id=org_id,
            course_id=data.course_id,
            academic_period_id=data.academic_period_id,
            teacher_id=data.teacher_id,
            code=data.code,
            capacity=data.capacity,
        )
        db.add(section)
        await db.flush()
        await db.refresh(section)
        return section

    @staticmethod
    async def get_section(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> EduSection:
        result = await db.execute(
            select(EduSection).where(
                EduSection.id == section_id,
                EduSection.organization_id == org_id,
            )
        )
        section = result.scalar_one_or_none()
        if section is None:
            raise NotFoundError("Section not found.")
        return section

    @staticmethod
    async def update_section(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID, data: SectionUpdate,
    ) -> EduSection:
        section = await EnrollmentService.get_section(db, org_id, section_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(section, field, value)
        await db.flush()
        await db.refresh(section)
        return section

    # ------------------------------------------------------------------
    # Enrollments
    # ------------------------------------------------------------------

    @staticmethod
    async def enroll_student(
        db: AsyncSession, org_id: uuid.UUID, data: EnrollmentCreate,
    ) -> EduEnrollment | EduWaitlist:
        section = await EnrollmentService.get_section(db, org_id, data.section_id)

        if section.status != "open":
            raise ValidationError("Section is not open for enrollment.")

        # Check duplicate
        existing = await db.execute(
            select(EduEnrollment).where(
                EduEnrollment.student_id == data.student_id,
                EduEnrollment.section_id == data.section_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Student is already enrolled in this section.")

        # Check capacity
        if section.enrolled_count >= section.capacity:
            # Add to waitlist
            count_result = await db.execute(
                select(func.count()).where(EduWaitlist.section_id == data.section_id)
            )
            position = (count_result.scalar() or 0) + 1
            waitlist = EduWaitlist(
                organization_id=org_id,
                student_id=data.student_id,
                section_id=data.section_id,
                position=position,
            )
            db.add(waitlist)
            await db.flush()
            await db.refresh(waitlist)
            return waitlist

        enrollment = EduEnrollment(
            organization_id=org_id,
            student_id=data.student_id,
            section_id=data.section_id,
        )
        db.add(enrollment)
        section.enrolled_count += 1
        await db.flush()
        await db.refresh(enrollment)
        return enrollment

    @staticmethod
    async def list_enrollments(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> list[EduEnrollment]:
        result = await db.execute(
            select(EduEnrollment).where(
                EduEnrollment.organization_id == org_id,
                EduEnrollment.section_id == section_id,
            ).order_by(EduEnrollment.enrolled_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_enrollment(
        db: AsyncSession, org_id: uuid.UUID, enrollment_id: uuid.UUID, data: EnrollmentUpdate,
    ) -> EduEnrollment:
        result = await db.execute(
            select(EduEnrollment).where(
                EduEnrollment.id == enrollment_id,
                EduEnrollment.organization_id == org_id,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise NotFoundError("Enrollment not found.")

        old_status = enrollment.status
        enrollment.status = data.status

        # Update enrolled_count if dropping
        if old_status == "enrolled" and data.status in ("dropped", "withdrawn"):
            section = await EnrollmentService.get_section(db, org_id, enrollment.section_id)
            section.enrolled_count = max(0, section.enrolled_count - 1)

        await db.flush()
        await db.refresh(enrollment)
        return enrollment

    @staticmethod
    async def list_waitlist(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> list[EduWaitlist]:
        result = await db.execute(
            select(EduWaitlist).where(
                EduWaitlist.organization_id == org_id,
                EduWaitlist.section_id == section_id,
            ).order_by(EduWaitlist.position)
        )
        return list(result.scalars().all())
