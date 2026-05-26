"""Lógica de traslados — workflow de estados + listing enriquecido."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialDriver,
    MemorialService,
    MemorialTransfer,
    MemorialVehicle,
)
from src.apps.memorial.transfers.schemas import (
    TransferCreate,
    TransferListItem,
    TransferTransitionRequest,
    TransferUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "scheduled": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def _vehicle_label(plate: str | None, brand: str | None, model: str | None) -> str | None:
    if not plate:
        return None
    parts = [plate]
    if brand or model:
        parts.append(f"({(brand or '').strip()} {(model or '').strip()}".strip() + ")")
    return " ".join(parts)


def _driver_name(first: str | None, last: str | None) -> str | None:
    if not first and not last:
        return None
    return f"{first or ''} {last or ''}".strip() or None


class TransfersService:

    @staticmethod
    async def _next_consecutive(db, org_id) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialTransfer.consecutive), 0))
            .where(MemorialTransfer.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    async def list_transfers(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[TransferListItem]:
        stmt = (
            select(
                MemorialTransfer,
                MemorialService.code.label("service_code"),
                MemorialService.deceased_first_name,
                MemorialService.deceased_last_name,
                MemorialVehicle.plate,
                MemorialVehicle.brand,
                MemorialVehicle.model,
                MemorialDriver.first_name.label("driver_first"),
                MemorialDriver.last_name.label("driver_last"),
            )
            .outerjoin(MemorialService, MemorialService.id == MemorialTransfer.service_id)
            .outerjoin(MemorialVehicle, MemorialVehicle.id == MemorialTransfer.vehicle_id)
            .outerjoin(MemorialDriver, MemorialDriver.id == MemorialTransfer.driver_id)
            .where(MemorialTransfer.organization_id == org_id)
            .order_by(MemorialTransfer.scheduled_at.desc())
            .limit(limit).offset(offset)
        )
        if service_id:
            stmt = stmt.where(MemorialTransfer.service_id == service_id)
        if status:
            stmt = stmt.where(MemorialTransfer.status == status)
        if date_from:
            stmt = stmt.where(MemorialTransfer.scheduled_at >= date_from)
        if date_to:
            stmt = stmt.where(MemorialTransfer.scheduled_at <= date_to)

        rows = await db.execute(stmt)
        out: list[TransferListItem] = []
        for r in rows.all():
            t = r[0]
            deceased = None
            if r[2]:
                deceased = f"{r[2]} {r[3] or ''}".strip()
            out.append(TransferListItem(
                id=t.id, code=t.code, consecutive=t.consecutive,
                service_id=t.service_id, service_code=r[1],
                deceased_name=deceased,
                transfer_type=t.transfer_type,
                vehicle_id=t.vehicle_id,
                vehicle_label=_vehicle_label(r[4], r[5], r[6]),
                driver_id=t.driver_id,
                driver_name=_driver_name(r[7], r[8]),
                scheduled_at=t.scheduled_at,
                completed_at=t.completed_at,
                origin=t.origin, destination=t.destination,
                status=t.status,
            ))
        return out

    @staticmethod
    async def get_transfer(
        db: AsyncSession, org_id: uuid.UUID, tid: uuid.UUID,
    ) -> MemorialTransfer:
        t = await db.scalar(
            select(MemorialTransfer).where(
                MemorialTransfer.id == tid,
                MemorialTransfer.organization_id == org_id,
            )
        )
        if t is None:
            raise NotFoundError("Traslado no encontrado.")
        return t

    @staticmethod
    async def create_transfer(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: TransferCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialTransfer:
        # Validar servicio si viene
        if data.service_id is not None:
            svc_exists = await db.scalar(
                select(MemorialService.id).where(
                    MemorialService.id == data.service_id,
                    MemorialService.organization_id == org_id,
                )
            )
            if svc_exists is None:
                raise NotFoundError("Servicio no encontrado.")

        consec = await TransfersService._next_consecutive(db, org_id)
        t = MemorialTransfer(
            organization_id=org_id,
            consecutive=consec,
            code=f"TRA-{consec:04d}",
            status="scheduled",
            created_by=actor_user_id,
            **data.model_dump(),
        )
        db.add(t)
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def update_transfer(
        db: AsyncSession,
        org_id: uuid.UUID,
        tid: uuid.UUID,
        data: TransferUpdate,
    ) -> MemorialTransfer:
        t = await TransfersService.get_transfer(db, org_id, tid)
        if t.status in ("completed", "cancelled"):
            raise ConflictError(
                "No se puede editar un traslado finalizado o cancelado.",
            )
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(t, k, v)
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def transition(
        db: AsyncSession,
        org_id: uuid.UUID,
        tid: uuid.UUID,
        req: TransferTransitionRequest,
    ) -> MemorialTransfer:
        t = await TransfersService.get_transfer(db, org_id, tid)
        old, new = t.status, req.new_status
        if new == old:
            raise ConflictError(f"El traslado ya está '{old}'.")
        allowed = LEGAL_TRANSITIONS.get(old, set())
        if new not in allowed:
            raise ValidationError(
                f"Transición no permitida: {old} → {new}.",
            )
        now = datetime.now(UTC)
        t.status = new
        if new == "in_progress":
            t.started_at = now
        elif new == "completed":
            t.completed_at = now
            if t.started_at is None:
                t.started_at = now
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def delete_transfer(
        db: AsyncSession, org_id: uuid.UUID, tid: uuid.UUID,
    ) -> None:
        t = await TransfersService.get_transfer(db, org_id, tid)
        if t.status in ("in_progress", "completed"):
            raise ConflictError(
                "No se puede eliminar un traslado en curso o completado. Cancélalo en su lugar.",
            )
        await db.delete(t)
        await db.flush()
