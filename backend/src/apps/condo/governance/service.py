"""Business logic for condo governance."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.condo.governance.models import CondoAssembly, CondoVote
from src.apps.condo.governance.schemas import AssemblyCreate, VoteCreate
from src.apps.condo.properties.models import CondoUnit


class GovernanceService:
    @staticmethod
    async def list_assemblies(db: AsyncSession, org_id: uuid.UUID) -> list[CondoAssembly]:
        return list((await db.execute(select(CondoAssembly).where(CondoAssembly.organization_id == org_id).order_by(CondoAssembly.scheduled_at.desc()))).scalars().all())

    @staticmethod
    async def create_assembly(db: AsyncSession, org_id: uuid.UUID, data: AssemblyCreate) -> CondoAssembly:
        a = CondoAssembly(organization_id=org_id, property_id=data.property_id, title=data.title,
            description=data.description, assembly_type=data.assembly_type,
            scheduled_at=data.scheduled_at, quorum_required=data.quorum_required,
            proposals=[p.model_dump() for p in data.proposals])
        db.add(a); await db.flush(); await db.refresh(a); return a

    @staticmethod
    async def cast_vote(db: AsyncSession, org_id: uuid.UUID, data: VoteCreate) -> CondoVote:
        # Get unit coefficient
        unit_result = await db.execute(select(CondoUnit).where(CondoUnit.id == data.unit_id))
        unit = unit_result.scalar_one_or_none()
        if unit is None: raise NotFoundError("Unit not found.")

        vote = CondoVote(organization_id=org_id, assembly_id=data.assembly_id,
            unit_id=data.unit_id, proposal_index=data.proposal_index,
            vote=data.vote, coefficient_weight=float(unit.coefficient))
        db.add(vote); await db.flush(); await db.refresh(vote); return vote

    @staticmethod
    async def get_vote_results(db: AsyncSession, assembly_id: uuid.UUID) -> list[CondoVote]:
        return list((await db.execute(select(CondoVote).where(CondoVote.assembly_id == assembly_id))).scalars().all())
