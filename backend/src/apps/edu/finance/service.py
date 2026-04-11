"""Business logic for SavvyEdu finance."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.edu.finance.models import (
    EduScholarship,
    EduScholarshipAward,
    EduStudentCharge,
    EduTuitionPlan,
)
from src.apps.edu.finance.schemas import (
    ScholarshipAwardCreate,
    ScholarshipCreate,
    StudentChargeCreate,
    TuitionPlanCreate,
)


class EduFinanceService:

    @staticmethod
    async def list_tuition_plans(db: AsyncSession, org_id: uuid.UUID) -> list[EduTuitionPlan]:
        result = await db.execute(
            select(EduTuitionPlan).where(EduTuitionPlan.organization_id == org_id)
            .order_by(EduTuitionPlan.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_tuition_plan(db: AsyncSession, org_id: uuid.UUID, data: TuitionPlanCreate) -> EduTuitionPlan:
        plan = EduTuitionPlan(
            organization_id=org_id,
            program_id=data.program_id,
            academic_period_id=data.academic_period_id,
            name=data.name,
            total_amount=data.total_amount,
            installments=[i.model_dump(mode='json') for i in data.installments],
        )
        db.add(plan)
        await db.flush()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def list_charges(db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID | None = None) -> list[EduStudentCharge]:
        q = select(EduStudentCharge).where(EduStudentCharge.organization_id == org_id)
        if student_id:
            q = q.where(EduStudentCharge.student_id == student_id)
        q = q.order_by(EduStudentCharge.due_date)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_charge(db: AsyncSession, org_id: uuid.UUID, data: StudentChargeCreate) -> EduStudentCharge:
        charge = EduStudentCharge(
            organization_id=org_id,
            student_id=data.student_id,
            tuition_plan_id=data.tuition_plan_id,
            description=data.description,
            amount=data.amount,
            balance=data.amount,
            due_date=data.due_date,
        )
        db.add(charge)
        await db.flush()
        await db.refresh(charge)
        return charge

    @staticmethod
    async def list_scholarships(db: AsyncSession, org_id: uuid.UUID) -> list[EduScholarship]:
        result = await db.execute(
            select(EduScholarship).where(EduScholarship.organization_id == org_id).order_by(EduScholarship.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_scholarship(db: AsyncSession, org_id: uuid.UUID, data: ScholarshipCreate) -> EduScholarship:
        sch = EduScholarship(
            organization_id=org_id,
            name=data.name,
            type=data.type,
            value=data.value,
            academic_period_id=data.academic_period_id,
        )
        db.add(sch)
        await db.flush()
        await db.refresh(sch)
        return sch

    @staticmethod
    async def award_scholarship(db: AsyncSession, org_id: uuid.UUID, data: ScholarshipAwardCreate) -> EduScholarshipAward:
        award = EduScholarshipAward(
            organization_id=org_id,
            scholarship_id=data.scholarship_id,
            student_id=data.student_id,
            applied_amount=data.applied_amount,
            academic_period_id=data.academic_period_id,
        )
        db.add(award)
        await db.flush()
        await db.refresh(award)
        return award
