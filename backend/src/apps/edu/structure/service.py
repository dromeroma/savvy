"""Business logic for SavvyEdu academic structure."""

from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.apps.edu.structure.models import (
    EduAcademicPeriod,
    EduCourse,
    EduCurriculumVersion,
    EduPrerequisite,
    EduProgram,
)
from src.apps.edu.structure.schemas import (
    AcademicPeriodCreate,
    AcademicPeriodUpdate,
    CourseCreate,
    CourseUpdate,
    CurriculumVersionCreate,
    CurriculumVersionUpdate,
    ProgramCreate,
    ProgramUpdate,
)


class AcademicStructureService:
    """CRUD for academic periods, programs, courses, and curricula."""

    # ------------------------------------------------------------------
    # Academic Periods
    # ------------------------------------------------------------------

    @staticmethod
    async def list_periods(
        db: AsyncSession, org_id: uuid.UUID, year: int | None = None,
    ) -> list[EduAcademicPeriod]:
        q = select(EduAcademicPeriod).where(EduAcademicPeriod.organization_id == org_id)
        if year:
            q = q.where(EduAcademicPeriod.year == year)
        q = q.order_by(EduAcademicPeriod.year.desc(), EduAcademicPeriod.start_date)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_period(
        db: AsyncSession, org_id: uuid.UUID, data: AcademicPeriodCreate,
    ) -> EduAcademicPeriod:
        if data.end_date <= data.start_date:
            raise ValidationError("End date must be after start date.")

        period = EduAcademicPeriod(
            organization_id=org_id,
            period_type_id=data.period_type_id,
            name=data.name,
            year=data.year,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        db.add(period)
        await db.flush()
        await db.refresh(period)
        return period

    @staticmethod
    async def get_period(
        db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID,
    ) -> EduAcademicPeriod:
        result = await db.execute(
            select(EduAcademicPeriod).where(
                EduAcademicPeriod.id == period_id,
                EduAcademicPeriod.organization_id == org_id,
            )
        )
        period = result.scalar_one_or_none()
        if period is None:
            raise NotFoundError("Academic period not found.")
        return period

    @staticmethod
    async def update_period(
        db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID, data: AcademicPeriodUpdate,
    ) -> EduAcademicPeriod:
        period = await AcademicStructureService.get_period(db, org_id, period_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(period, field, value)
        await db.flush()
        await db.refresh(period)
        return period

    # ------------------------------------------------------------------
    # Programs
    # ------------------------------------------------------------------

    @staticmethod
    async def list_programs(
        db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None,
    ) -> list[EduProgram]:
        q = select(EduProgram).where(EduProgram.organization_id == org_id)
        if status_filter:
            q = q.where(EduProgram.status == status_filter)
        q = q.order_by(EduProgram.name)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_program(
        db: AsyncSession, org_id: uuid.UUID, data: ProgramCreate,
    ) -> EduProgram:
        program = EduProgram(
            organization_id=org_id,
            scope_id=data.scope_id,
            grading_system_id=data.grading_system_id,
            evaluation_template_id=data.evaluation_template_id,
            code=data.code,
            name=data.name,
            degree_type=data.degree_type,
            duration_periods=data.duration_periods,
            credits_required=data.credits_required,
            description=data.description,
        )
        db.add(program)
        await db.flush()
        await db.refresh(program)
        return program

    @staticmethod
    async def get_program(
        db: AsyncSession, org_id: uuid.UUID, program_id: uuid.UUID,
    ) -> EduProgram:
        result = await db.execute(
            select(EduProgram).where(
                EduProgram.id == program_id,
                EduProgram.organization_id == org_id,
            )
        )
        program = result.scalar_one_or_none()
        if program is None:
            raise NotFoundError("Program not found.")
        return program

    @staticmethod
    async def update_program(
        db: AsyncSession, org_id: uuid.UUID, program_id: uuid.UUID, data: ProgramUpdate,
    ) -> EduProgram:
        program = await AcademicStructureService.get_program(db, org_id, program_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(program, field, value)
        await db.flush()
        await db.refresh(program)
        return program

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    @staticmethod
    async def list_courses(
        db: AsyncSession,
        org_id: uuid.UUID,
        program_id: uuid.UUID | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[EduCourse], int]:
        q = select(EduCourse).where(EduCourse.organization_id == org_id)
        if program_id:
            q = q.where(EduCourse.program_id == program_id)
        if search:
            term = f"%{search}%"
            from sqlalchemy import or_
            q = q.where(or_(EduCourse.code.ilike(term), EduCourse.name.ilike(term)))

        count_result = await db.execute(select(func.count()).select_from(q.subquery()))
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await db.execute(q.order_by(EduCourse.code).offset(offset).limit(page_size))
        return list(result.scalars().all()), total

    @staticmethod
    async def create_course(
        db: AsyncSession, org_id: uuid.UUID, data: CourseCreate,
    ) -> EduCourse:
        course = EduCourse(
            organization_id=org_id,
            program_id=data.program_id,
            code=data.code,
            name=data.name,
            credits=data.credits,
            weekly_hours=data.weekly_hours,
            is_elective=data.is_elective,
            description=data.description,
        )
        db.add(course)
        await db.flush()

        for prereq in data.prerequisites:
            p = EduPrerequisite(
                course_id=course.id,
                prerequisite_id=prereq.prerequisite_id,
                min_grade=prereq.min_grade,
            )
            db.add(p)

        await db.flush()
        await db.refresh(course)
        return course

    @staticmethod
    async def get_course(
        db: AsyncSession, org_id: uuid.UUID, course_id: uuid.UUID,
    ) -> EduCourse:
        result = await db.execute(
            select(EduCourse).where(
                EduCourse.id == course_id,
                EduCourse.organization_id == org_id,
            )
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("Course not found.")
        return course

    @staticmethod
    async def update_course(
        db: AsyncSession, org_id: uuid.UUID, course_id: uuid.UUID, data: CourseUpdate,
    ) -> EduCourse:
        course = await AcademicStructureService.get_course(db, org_id, course_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        await db.flush()
        await db.refresh(course)
        return course

    # ------------------------------------------------------------------
    # Curriculum Versions
    # ------------------------------------------------------------------

    @staticmethod
    async def list_curriculum_versions(
        db: AsyncSession, program_id: uuid.UUID,
    ) -> list[EduCurriculumVersion]:
        result = await db.execute(
            select(EduCurriculumVersion)
            .where(EduCurriculumVersion.program_id == program_id)
            .order_by(EduCurriculumVersion.effective_from.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_curriculum_version(
        db: AsyncSession, data: CurriculumVersionCreate,
    ) -> EduCurriculumVersion:
        cv = EduCurriculumVersion(
            program_id=data.program_id,
            version=data.version,
            effective_from=data.effective_from,
            course_map=data.course_map,
        )
        db.add(cv)
        await db.flush()
        await db.refresh(cv)
        return cv

    @staticmethod
    async def update_curriculum_version(
        db: AsyncSession, cv_id: uuid.UUID, data: CurriculumVersionUpdate,
    ) -> EduCurriculumVersion:
        result = await db.execute(
            select(EduCurriculumVersion).where(EduCurriculumVersion.id == cv_id)
        )
        cv = result.scalar_one_or_none()
        if cv is None:
            raise NotFoundError("Curriculum version not found.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cv, field, value)
        await db.flush()
        await db.refresh(cv)
        return cv
