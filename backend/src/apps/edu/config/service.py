"""Business logic for SavvyEdu institutional configuration."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.apps.edu.config.models import (
    EduAcademicPeriodType,
    EduEvaluationTemplate,
    EduGradeScale,
    EduGradingSystem,
)
from src.apps.edu.config.schemas import (
    AcademicPeriodTypeCreate,
    AcademicPeriodTypeUpdate,
    EvaluationTemplateCreate,
    EvaluationTemplateUpdate,
    GradingSystemCreate,
    GradingSystemUpdate,
)


class EduConfigService:
    """CRUD operations for SavvyEdu configuration entities."""

    # ------------------------------------------------------------------
    # Grading Systems
    # ------------------------------------------------------------------

    @staticmethod
    async def list_grading_systems(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[EduGradingSystem]:
        result = await db.execute(
            select(EduGradingSystem)
            .where(EduGradingSystem.organization_id == org_id)
            .order_by(EduGradingSystem.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_grading_system(
        db: AsyncSession, org_id: uuid.UUID, data: GradingSystemCreate,
    ) -> EduGradingSystem:
        gs = EduGradingSystem(
            organization_id=org_id,
            name=data.name,
            type=data.type,
            scale_min=data.scale_min,
            scale_max=data.scale_max,
            passing_grade=data.passing_grade,
            is_default=data.is_default,
        )
        db.add(gs)
        await db.flush()

        for s in data.scales:
            scale = EduGradeScale(
                grading_system_id=gs.id,
                label=s.label,
                min_value=s.min_value,
                max_value=s.max_value,
                gpa_value=s.gpa_value,
                is_passing=s.is_passing,
                sort_order=s.sort_order,
            )
            db.add(scale)

        await db.flush()
        await db.refresh(gs)
        return gs

    @staticmethod
    async def get_grading_system(
        db: AsyncSession, org_id: uuid.UUID, gs_id: uuid.UUID,
    ) -> EduGradingSystem:
        result = await db.execute(
            select(EduGradingSystem).where(
                EduGradingSystem.id == gs_id,
                EduGradingSystem.organization_id == org_id,
            )
        )
        gs = result.scalar_one_or_none()
        if gs is None:
            raise NotFoundError("Grading system not found.")
        return gs

    @staticmethod
    async def update_grading_system(
        db: AsyncSession, org_id: uuid.UUID, gs_id: uuid.UUID, data: GradingSystemUpdate,
    ) -> EduGradingSystem:
        gs = await EduConfigService.get_grading_system(db, org_id, gs_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(gs, field, value)
        await db.flush()
        await db.refresh(gs)
        return gs

    @staticmethod
    async def delete_grading_system(
        db: AsyncSession, org_id: uuid.UUID, gs_id: uuid.UUID,
    ) -> None:
        gs = await EduConfigService.get_grading_system(db, org_id, gs_id)
        await db.delete(gs)
        await db.flush()

    # ------------------------------------------------------------------
    # Academic Period Types
    # ------------------------------------------------------------------

    @staticmethod
    async def list_period_types(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[EduAcademicPeriodType]:
        result = await db.execute(
            select(EduAcademicPeriodType)
            .where(EduAcademicPeriodType.organization_id == org_id)
            .order_by(EduAcademicPeriodType.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_period_type(
        db: AsyncSession, org_id: uuid.UUID, data: AcademicPeriodTypeCreate,
    ) -> EduAcademicPeriodType:
        existing = await db.execute(
            select(EduAcademicPeriodType).where(
                EduAcademicPeriodType.organization_id == org_id,
                EduAcademicPeriodType.code == data.code,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Period type '{data.code}' already exists.")

        pt = EduAcademicPeriodType(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            default_duration_weeks=data.default_duration_weeks,
        )
        db.add(pt)
        await db.flush()
        await db.refresh(pt)
        return pt

    @staticmethod
    async def update_period_type(
        db: AsyncSession, org_id: uuid.UUID, pt_id: uuid.UUID, data: AcademicPeriodTypeUpdate,
    ) -> EduAcademicPeriodType:
        result = await db.execute(
            select(EduAcademicPeriodType).where(
                EduAcademicPeriodType.id == pt_id,
                EduAcademicPeriodType.organization_id == org_id,
            )
        )
        pt = result.scalar_one_or_none()
        if pt is None:
            raise NotFoundError("Academic period type not found.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pt, field, value)
        await db.flush()
        await db.refresh(pt)
        return pt

    # ------------------------------------------------------------------
    # Evaluation Templates
    # ------------------------------------------------------------------

    @staticmethod
    async def list_evaluation_templates(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[EduEvaluationTemplate]:
        result = await db.execute(
            select(EduEvaluationTemplate)
            .where(EduEvaluationTemplate.organization_id == org_id)
            .order_by(EduEvaluationTemplate.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_evaluation_template(
        db: AsyncSession, org_id: uuid.UUID, data: EvaluationTemplateCreate,
    ) -> EduEvaluationTemplate:
        total_weight = sum(c.weight for c in data.components)
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationError(f"Component weights must sum to 1.0 (got {total_weight:.2f}).")

        et = EduEvaluationTemplate(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            components=[c.model_dump() for c in data.components],
            is_default=data.is_default,
        )
        db.add(et)
        await db.flush()
        await db.refresh(et)
        return et

    @staticmethod
    async def update_evaluation_template(
        db: AsyncSession, org_id: uuid.UUID, et_id: uuid.UUID, data: EvaluationTemplateUpdate,
    ) -> EduEvaluationTemplate:
        result = await db.execute(
            select(EduEvaluationTemplate).where(
                EduEvaluationTemplate.id == et_id,
                EduEvaluationTemplate.organization_id == org_id,
            )
        )
        et = result.scalar_one_or_none()
        if et is None:
            raise NotFoundError("Evaluation template not found.")

        update_data = data.model_dump(exclude_unset=True)
        if "components" in update_data and update_data["components"] is not None:
            total_weight = sum(c["weight"] for c in update_data["components"])
            if abs(total_weight - 1.0) > 0.01:
                raise ValidationError(f"Component weights must sum to 1.0 (got {total_weight:.2f}).")

        for field, value in update_data.items():
            setattr(et, field, value)
        await db.flush()
        await db.refresh(et)
        return et
