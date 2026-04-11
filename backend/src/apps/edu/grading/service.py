"""Business logic for SavvyEdu grading — evaluations, grades, GradingEngine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.apps.edu.grading.models import EduEvaluation, EduFinalGrade, EduGrade
from src.apps.edu.grading.schemas import (
    BulkGradeCreate,
    EvaluationCreate,
    EvaluationUpdate,
    GradeCreate,
)
from src.apps.edu.config.models import EduGradeScale, EduGradingSystem
from src.apps.edu.enrollment.models import EduEnrollment, EduSection
from src.apps.edu.structure.models import EduProgram


class GradingService:
    """Evaluations, grades, and final grade calculation."""

    # ------------------------------------------------------------------
    # Evaluations
    # ------------------------------------------------------------------

    @staticmethod
    async def list_evaluations(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> list[EduEvaluation]:
        result = await db.execute(
            select(EduEvaluation).where(
                EduEvaluation.organization_id == org_id,
                EduEvaluation.section_id == section_id,
            ).order_by(EduEvaluation.due_date, EduEvaluation.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_evaluation(
        db: AsyncSession, org_id: uuid.UUID, data: EvaluationCreate,
    ) -> EduEvaluation:
        ev = EduEvaluation(
            organization_id=org_id,
            section_id=data.section_id,
            name=data.name,
            type=data.type,
            weight=data.weight,
            max_score=data.max_score,
            due_date=data.due_date,
        )
        db.add(ev)
        await db.flush()
        await db.refresh(ev)
        return ev

    @staticmethod
    async def update_evaluation(
        db: AsyncSession, org_id: uuid.UUID, eval_id: uuid.UUID, data: EvaluationUpdate,
    ) -> EduEvaluation:
        result = await db.execute(
            select(EduEvaluation).where(
                EduEvaluation.id == eval_id,
                EduEvaluation.organization_id == org_id,
            )
        )
        ev = result.scalar_one_or_none()
        if ev is None:
            raise NotFoundError("Evaluation not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ev, field, value)
        await db.flush()
        await db.refresh(ev)
        return ev

    # ------------------------------------------------------------------
    # Grades
    # ------------------------------------------------------------------

    @staticmethod
    async def record_grades(
        db: AsyncSession, org_id: uuid.UUID, data: BulkGradeCreate,
    ) -> list[EduGrade]:
        ev_result = await db.execute(
            select(EduEvaluation).where(
                EduEvaluation.id == data.evaluation_id,
                EduEvaluation.organization_id == org_id,
            )
        )
        ev = ev_result.scalar_one_or_none()
        if ev is None:
            raise NotFoundError("Evaluation not found.")

        results = []
        now = datetime.now(UTC)
        for g in data.grades:
            percentage = (g.score / float(ev.max_score)) * 100 if float(ev.max_score) > 0 else 0

            existing = await db.execute(
                select(EduGrade).where(
                    EduGrade.evaluation_id == data.evaluation_id,
                    EduGrade.student_id == g.student_id,
                )
            )
            grade = existing.scalar_one_or_none()
            if grade:
                grade.score = g.score
                grade.percentage = percentage
                grade.comments = g.comments
                grade.graded_at = now
            else:
                grade = EduGrade(
                    organization_id=org_id,
                    evaluation_id=data.evaluation_id,
                    student_id=g.student_id,
                    score=g.score,
                    percentage=percentage,
                    comments=g.comments,
                    graded_at=now,
                )
                db.add(grade)
            results.append(grade)

        await db.flush()
        for grade in results:
            await db.refresh(grade)
        return results

    @staticmethod
    async def list_grades(
        db: AsyncSession, org_id: uuid.UUID, evaluation_id: uuid.UUID,
    ) -> list[EduGrade]:
        result = await db.execute(
            select(EduGrade).where(
                EduGrade.organization_id == org_id,
                EduGrade.evaluation_id == evaluation_id,
            ).order_by(EduGrade.student_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # GradingEngine: Calculate final grades
    # ------------------------------------------------------------------

    @staticmethod
    async def calculate_final_grades(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> list[EduFinalGrade]:
        """Calculate weighted final grades for all enrolled students in a section."""
        # Get section + period + program's grading system
        section_result = await db.execute(
            select(EduSection).where(EduSection.id == section_id)
        )
        section = section_result.scalar_one_or_none()
        if section is None:
            raise NotFoundError("Section not found.")

        # Get evaluations for this section
        evals_result = await db.execute(
            select(EduEvaluation).where(
                EduEvaluation.section_id == section_id,
                EduEvaluation.status == "active",
            )
        )
        evaluations = list(evals_result.scalars().all())
        if not evaluations:
            raise ValidationError("No active evaluations found for this section.")

        # Get enrolled students
        enrollments_result = await db.execute(
            select(EduEnrollment).where(
                EduEnrollment.section_id == section_id,
                EduEnrollment.status == "enrolled",
            )
        )
        enrollments = list(enrollments_result.scalars().all())

        # Try to get grading system from program
        grading_system = None
        from src.apps.edu.structure.models import EduCourse
        course_result = await db.execute(
            select(EduCourse).where(EduCourse.id == section.course_id)
        )
        course = course_result.scalar_one_or_none()
        if course and course.program_id:
            program_result = await db.execute(
                select(EduProgram).where(EduProgram.id == course.program_id)
            )
            program = program_result.scalar_one_or_none()
            if program and program.grading_system_id:
                gs_result = await db.execute(
                    select(EduGradingSystem).where(EduGradingSystem.id == program.grading_system_id)
                )
                grading_system = gs_result.scalar_one_or_none()

        # If no program grading system, try org default
        if grading_system is None:
            gs_result = await db.execute(
                select(EduGradingSystem).where(
                    EduGradingSystem.organization_id == org_id,
                    EduGradingSystem.is_default == True,
                )
            )
            grading_system = gs_result.scalar_one_or_none()

        # Get scales if we have a grading system
        scales = []
        if grading_system:
            scales_result = await db.execute(
                select(EduGradeScale).where(
                    EduGradeScale.grading_system_id == grading_system.id,
                ).order_by(EduGradeScale.min_value.desc())
            )
            scales = list(scales_result.scalars().all())

        results = []
        for enrollment in enrollments:
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0

            for ev in evaluations:
                grade_result = await db.execute(
                    select(EduGrade).where(
                        EduGrade.evaluation_id == ev.id,
                        EduGrade.student_id == enrollment.student_id,
                    )
                )
                grade = grade_result.scalar_one_or_none()
                if grade:
                    pct = float(grade.percentage or 0)
                    w = float(ev.weight)
                    weighted_sum += pct * w
                    total_weight += w

            numeric_grade = weighted_sum / total_weight if total_weight > 0 else 0

            # Convert to scale
            if grading_system:
                scale_min = float(grading_system.scale_min)
                scale_max = float(grading_system.scale_max)
                numeric_grade = scale_min + (numeric_grade / 100) * (scale_max - scale_min)

            # Find letter grade
            letter_grade = None
            gpa_points = None
            passing = float(grading_system.passing_grade) if grading_system else 60

            for scale in scales:
                if float(scale.min_value) <= numeric_grade <= float(scale.max_value):
                    letter_grade = scale.label
                    gpa_points = float(scale.gpa_value) if scale.gpa_value else None
                    break

            status = "approved" if numeric_grade >= passing else "failed"

            # Upsert final grade
            existing = await db.execute(
                select(EduFinalGrade).where(
                    EduFinalGrade.student_id == enrollment.student_id,
                    EduFinalGrade.section_id == section_id,
                )
            )
            final = existing.scalar_one_or_none()
            if final:
                final.numeric_grade = round(numeric_grade, 2)
                final.letter_grade = letter_grade
                final.gpa_points = gpa_points
                final.status = status
            else:
                final = EduFinalGrade(
                    organization_id=org_id,
                    student_id=enrollment.student_id,
                    section_id=section_id,
                    academic_period_id=section.academic_period_id,
                    numeric_grade=round(numeric_grade, 2),
                    letter_grade=letter_grade,
                    gpa_points=gpa_points,
                    status=status,
                )
                db.add(final)
            results.append(final)

        await db.flush()
        for fg in results:
            await db.refresh(fg)
        return results

    @staticmethod
    async def list_final_grades(
        db: AsyncSession, org_id: uuid.UUID, section_id: uuid.UUID,
    ) -> list[EduFinalGrade]:
        result = await db.execute(
            select(EduFinalGrade).where(
                EduFinalGrade.organization_id == org_id,
                EduFinalGrade.section_id == section_id,
            ).order_by(EduFinalGrade.student_id)
        )
        return list(result.scalars().all())
