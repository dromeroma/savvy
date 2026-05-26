"""Lógica de negocio para planes exequiales."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialExequialContract,
    MemorialExequialPlan,
)
from src.apps.memorial.plans.schemas import (
    PlanCreate,
    PlanListItem,
    PlanUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError


class PlansService:

    @staticmethod
    async def list_plans(
        db: AsyncSession,
        org_id: uuid.UUID,
        active_only: bool = False,
        search: str | None = None,
    ) -> list[PlanListItem]:
        contracts_count_sq = (
            select(
                MemorialExequialContract.plan_id,
                func.count(MemorialExequialContract.id).label("n"),
            )
            .where(
                MemorialExequialContract.organization_id == org_id,
                MemorialExequialContract.status == "active",
            )
            .group_by(MemorialExequialContract.plan_id)
            .subquery()
        )
        stmt = (
            select(
                MemorialExequialPlan.id,
                MemorialExequialPlan.code,
                MemorialExequialPlan.name,
                MemorialExequialPlan.plan_type,
                MemorialExequialPlan.monthly_fee,
                MemorialExequialPlan.coverage_amount,
                MemorialExequialPlan.is_active,
                func.coalesce(contracts_count_sq.c.n, 0).label("contracts_count"),
            )
            .outerjoin(contracts_count_sq, contracts_count_sq.c.plan_id == MemorialExequialPlan.id)
            .where(MemorialExequialPlan.organization_id == org_id)
            .order_by(MemorialExequialPlan.code)
        )
        if active_only:
            stmt = stmt.where(MemorialExequialPlan.is_active.is_(True))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialExequialPlan.code).like(like),
                    func.lower(MemorialExequialPlan.name).like(like),
                )
            )
        rows = await db.execute(stmt)
        return [
            PlanListItem(
                id=r[0], code=r[1], name=r[2], plan_type=r[3],
                monthly_fee=r[4], coverage_amount=r[5], is_active=r[6],
                contracts_count=int(r[7]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_plan(
        db: AsyncSession, org_id: uuid.UUID, plan_id: uuid.UUID,
    ) -> MemorialExequialPlan:
        p = await db.scalar(
            select(MemorialExequialPlan).where(
                MemorialExequialPlan.id == plan_id,
                MemorialExequialPlan.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Plan exequial no encontrado.")
        return p

    @staticmethod
    async def create_plan(
        db: AsyncSession, org_id: uuid.UUID, data: PlanCreate,
    ) -> MemorialExequialPlan:
        existing = await db.scalar(
            select(MemorialExequialPlan).where(
                MemorialExequialPlan.organization_id == org_id,
                MemorialExequialPlan.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un plan con código '{data.code}'.")
        p = MemorialExequialPlan(organization_id=org_id, **data.model_dump())
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def update_plan(
        db: AsyncSession, org_id: uuid.UUID, plan_id: uuid.UUID, data: PlanUpdate,
    ) -> MemorialExequialPlan:
        p = await PlansService.get_plan(db, org_id, plan_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def delete_plan(
        db: AsyncSession, org_id: uuid.UUID, plan_id: uuid.UUID,
    ) -> None:
        # Bloqueamos si hay contratos vivos
        in_use = await db.scalar(
            select(func.count(MemorialExequialContract.id)).where(
                MemorialExequialContract.plan_id == plan_id,
                MemorialExequialContract.organization_id == org_id,
            )
        )
        if in_use and int(in_use) > 0:
            raise ConflictError(
                f"Este plan tiene {int(in_use)} contrato(s) — desactívalo en vez de eliminarlo.",
            )
        p = await PlansService.get_plan(db, org_id, plan_id)
        await db.delete(p)
        await db.flush()
