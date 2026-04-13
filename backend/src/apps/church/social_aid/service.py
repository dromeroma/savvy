"""Business logic for social aid sub-module."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.church.social_aid.models import (
    ChurchAidBeneficiary,
    ChurchAidDistribution,
    ChurchAidProgram,
)
from src.apps.church.social_aid.schemas import (
    AidProgramCreate,
    AidProgramUpdate,
    BeneficiaryCreate,
    BeneficiaryUpdate,
    DistributionCreate,
)


class AidProgramService:

    @staticmethod
    async def list_programs(
        db: AsyncSession, org_id: uuid.UUID,
        status: str | None = None,
    ) -> list[ChurchAidProgram]:
        stmt = (
            select(ChurchAidProgram)
            .where(ChurchAidProgram.organization_id == org_id)
            .order_by(ChurchAidProgram.start_date.desc().nullslast())
        )
        if status:
            stmt = stmt.where(ChurchAidProgram.status == status)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_program(
        db: AsyncSession, org_id: uuid.UUID, program_id: uuid.UUID,
    ) -> ChurchAidProgram:
        program = await db.get(ChurchAidProgram, program_id)
        if program is None or program.organization_id != org_id:
            raise NotFoundError("Aid program not found.")
        return program

    @staticmethod
    async def create_program(
        db: AsyncSession, org_id: uuid.UUID, data: AidProgramCreate,
    ) -> ChurchAidProgram:
        program = ChurchAidProgram(organization_id=org_id, **data.model_dump())
        db.add(program)
        await db.flush()
        await db.refresh(program)
        return program

    @staticmethod
    async def update_program(
        db: AsyncSession, org_id: uuid.UUID,
        program_id: uuid.UUID, data: AidProgramUpdate,
    ) -> ChurchAidProgram:
        program = await AidProgramService.get_program(db, org_id, program_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(program, field, value)
        await db.flush()
        await db.refresh(program)
        return program


class BeneficiaryService:

    @staticmethod
    async def list_for_program(
        db: AsyncSession, org_id: uuid.UUID, program_id: uuid.UUID,
    ) -> list[ChurchAidBeneficiary]:
        result = await db.execute(
            select(ChurchAidBeneficiary)
            .where(
                ChurchAidBeneficiary.organization_id == org_id,
                ChurchAidBeneficiary.program_id == program_id,
            )
            .order_by(ChurchAidBeneficiary.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_beneficiary(
        db: AsyncSession, org_id: uuid.UUID, data: BeneficiaryCreate,
    ) -> ChurchAidBeneficiary:
        beneficiary = ChurchAidBeneficiary(organization_id=org_id, **data.model_dump())
        db.add(beneficiary)
        await db.flush()
        await db.refresh(beneficiary)
        return beneficiary

    @staticmethod
    async def update_beneficiary(
        db: AsyncSession, org_id: uuid.UUID,
        beneficiary_id: uuid.UUID, data: BeneficiaryUpdate,
    ) -> ChurchAidBeneficiary:
        b = await db.get(ChurchAidBeneficiary, beneficiary_id)
        if b is None or b.organization_id != org_id:
            raise NotFoundError("Beneficiary not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(b, field, value)
        await db.flush()
        await db.refresh(b)
        return b


class DistributionService:

    @staticmethod
    async def list_for_program(
        db: AsyncSession, org_id: uuid.UUID, program_id: uuid.UUID,
    ) -> list[ChurchAidDistribution]:
        result = await db.execute(
            select(ChurchAidDistribution)
            .where(
                ChurchAidDistribution.organization_id == org_id,
                ChurchAidDistribution.program_id == program_id,
            )
            .order_by(ChurchAidDistribution.distribution_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_distribution(
        db: AsyncSession, org_id: uuid.UUID, data: DistributionCreate,
    ) -> ChurchAidDistribution:
        dist = ChurchAidDistribution(organization_id=org_id, **data.model_dump())
        db.add(dist)
        await db.flush()
        await db.refresh(dist)
        return dist
