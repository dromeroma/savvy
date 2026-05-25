"""PQRS service — admin operations on Peticiones/Quejas/Reclamos/Sugerencias."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterPqrs, WaterSubscriber
from src.apps.water.pqrs.schemas import (
    AdminPqrsCreate,
    PqrsCreate,
    PqrsListItem,
    PqrsRespond,
    PqrsStatusUpdate,
)
from src.core.exceptions import NotFoundError, ValidationError


class PqrsService:

    @staticmethod
    async def list_pqrs(
        db: AsyncSession,
        org_id: uuid.UUID,
        status_: str | None = None,
        type_: str | None = None,
        subscriber_id: uuid.UUID | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[PqrsListItem]:
        stmt = (
            select(
                WaterPqrs.id, WaterPqrs.code, WaterPqrs.type, WaterPqrs.subject,
                WaterPqrs.status, WaterPqrs.subscriber_id,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
                WaterPqrs.created_at, WaterPqrs.responded_at,
            )
            .join(WaterSubscriber, WaterSubscriber.id == WaterPqrs.subscriber_id)
            .where(WaterPqrs.organization_id == org_id)
            .order_by(WaterPqrs.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status_:
            stmt = stmt.where(WaterPqrs.status == status_)
        if type_:
            stmt = stmt.where(WaterPqrs.type == type_)
        if subscriber_id is not None:
            stmt = stmt.where(WaterPqrs.subscriber_id == subscriber_id)
        rows = await db.execute(stmt)
        return [
            PqrsListItem(
                id=r[0], code=r[1], type=r[2], subject=r[3], status=r[4],
                subscriber_id=r[5], subscriber_code=r[6],
                subscriber_name=(r[7].strip() if r[7] else ""),
                created_at=r[8], responded_at=r[9],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_pqrs(
        db: AsyncSession, org_id: uuid.UUID, pqrs_id: uuid.UUID,
        subscriber_id: uuid.UUID | None = None,
    ) -> WaterPqrs:
        stmt = select(WaterPqrs).where(
            WaterPqrs.id == pqrs_id, WaterPqrs.organization_id == org_id,
        )
        if subscriber_id is not None:
            stmt = stmt.where(WaterPqrs.subscriber_id == subscriber_id)
        p = await db.scalar(stmt)
        if p is None:
            raise NotFoundError("PQRS not found.")
        return p

    @staticmethod
    async def create_pqrs(
        db: AsyncSession,
        org_id: uuid.UUID,
        subscriber_id: uuid.UUID,
        data: PqrsCreate | AdminPqrsCreate,
        created_by: uuid.UUID | None,
    ) -> WaterPqrs:
        # Verify subscriber belongs to the org
        sub = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.id == subscriber_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if sub is None:
            raise NotFoundError("Subscriber not found.")

        code = await PqrsService._next_code(db, org_id)
        p = WaterPqrs(
            organization_id=org_id,
            subscriber_id=subscriber_id,
            code=code,
            type=data.type,
            subject=data.subject,
            description=data.description,
            status="open",
            created_by=created_by,
        )
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def respond_pqrs(
        db: AsyncSession,
        org_id: uuid.UUID,
        pqrs_id: uuid.UUID,
        data: PqrsRespond,
        responded_by: uuid.UUID | None,
    ) -> WaterPqrs:
        p = await PqrsService.get_pqrs(db, org_id, pqrs_id)
        if p.status == "closed":
            raise ValidationError("Esta PQRS ya está cerrada.")
        p.response = data.response
        p.status = data.status
        p.responded_by = responded_by
        p.responded_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def update_status(
        db: AsyncSession,
        org_id: uuid.UUID,
        pqrs_id: uuid.UUID,
        data: PqrsStatusUpdate,
    ) -> WaterPqrs:
        p = await PqrsService.get_pqrs(db, org_id, pqrs_id)
        p.status = data.status
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def _next_code(db: AsyncSession, org_id: uuid.UUID) -> str:
        year = datetime.now(UTC).year
        prefix = f"PQRS-{year}-"
        last = await db.scalar(
            select(func.count(WaterPqrs.id)).where(
                WaterPqrs.organization_id == org_id,
                WaterPqrs.code.like(f"{prefix}%"),
            )
        )
        n = (int(last) if last else 0) + 1
        return f"{prefix}{n:05d}"
