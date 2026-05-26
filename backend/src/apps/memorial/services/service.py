"""Business logic para servicios funerarios + dashboard ejecutivo de
SavvyMemorial fase 1."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialService,
    MemorialServiceEvent,
    MemorialServiceFamily,
)
from src.apps.memorial.services.schemas import (
    AddNoteRequest,
    DashboardKpis,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    ServiceCreate,
    ServiceListItem,
    ServiceUpdate,
    StatusTransitionRequest,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


# Transiciones legales del workflow de servicios. Origen → destinos permitidos.
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "iniciado": {"en_proceso", "pendiente", "cancelado"},
    "en_proceso": {"pendiente", "finalizado", "cancelado"},
    "pendiente": {"en_proceso", "finalizado", "cancelado"},
    "finalizado": set(),     # terminal
    "cancelado": set(),      # terminal
}


def _deceased_full_name(s: MemorialService) -> str:
    return f"{s.deceased_first_name} {s.deceased_last_name or ''}".strip()


class MemorialServicesService:

    # ------------------------------------------------------------------
    # Listing / detail
    # ------------------------------------------------------------------
    @staticmethod
    async def list_services(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
        service_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ServiceListItem]:
        # Subquery: contar familiares y traer el "primary"
        family_count_sq = (
            select(
                MemorialServiceFamily.service_id,
                func.count(MemorialServiceFamily.id).label("n"),
            )
            .where(MemorialServiceFamily.organization_id == org_id)
            .group_by(MemorialServiceFamily.service_id)
            .subquery()
        )

        # Primary family member (one row max per service: is_primary=true)
        primary_fam_sq = (
            select(
                MemorialServiceFamily.service_id,
                MemorialServiceFamily.first_name,
                MemorialServiceFamily.last_name,
                MemorialServiceFamily.mobile,
                MemorialServiceFamily.phone,
            )
            .where(
                MemorialServiceFamily.organization_id == org_id,
                MemorialServiceFamily.is_primary.is_(True),
            )
            .subquery()
        )

        stmt = (
            select(
                MemorialService.id,
                MemorialService.code,
                MemorialService.consecutive,
                MemorialService.deceased_first_name,
                MemorialService.deceased_last_name,
                MemorialService.deceased_death_date,
                MemorialService.service_type,
                MemorialService.status,
                MemorialService.estimated_total,
                MemorialService.final_total,
                MemorialService.created_at,
                func.coalesce(family_count_sq.c.n, 0).label("family_count"),
                primary_fam_sq.c.first_name.label("p_first"),
                primary_fam_sq.c.last_name.label("p_last"),
                func.coalesce(primary_fam_sq.c.mobile, primary_fam_sq.c.phone).label("p_phone"),
            )
            .outerjoin(family_count_sq, family_count_sq.c.service_id == MemorialService.id)
            .outerjoin(primary_fam_sq, primary_fam_sq.c.service_id == MemorialService.id)
            .where(MemorialService.organization_id == org_id)
            .order_by(MemorialService.consecutive.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(MemorialService.status == status)
        if service_type:
            stmt = stmt.where(MemorialService.service_type == service_type)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialService.code).like(like),
                    func.lower(MemorialService.deceased_first_name).like(like),
                    func.lower(func.coalesce(MemorialService.deceased_last_name, "")).like(like),
                    func.lower(func.coalesce(MemorialService.deceased_document_number, "")).like(like),
                )
            )

        rows = await db.execute(stmt)
        out: list[ServiceListItem] = []
        for r in rows.all():
            deceased = f"{r[3]} {r[4] or ''}".strip()
            primary_name = (
                f"{r[12]} {r[13] or ''}".strip() if r[12] else None
            )
            out.append(ServiceListItem(
                id=r[0], code=r[1], consecutive=r[2],
                deceased_name=deceased,
                deceased_death_date=r[5],
                service_type=r[6], status=r[7],
                estimated_total=r[8], final_total=r[9],
                created_at=r[10],
                family_count=int(r[11]),
                primary_family_name=primary_name,
                primary_family_phone=r[14],
            ))
        return out

    @staticmethod
    async def get_service(
        db: AsyncSession, org_id: uuid.UUID, service_id: uuid.UUID,
    ) -> MemorialService:
        svc = await db.scalar(
            select(MemorialService).where(
                MemorialService.id == service_id,
                MemorialService.organization_id == org_id,
            )
        )
        if svc is None:
            raise NotFoundError("Servicio funerario no encontrado.")
        return svc

    @staticmethod
    async def get_service_with_family(
        db: AsyncSession, org_id: uuid.UUID, service_id: uuid.UUID,
    ) -> tuple[MemorialService, list[MemorialServiceFamily]]:
        svc = await MemorialServicesService.get_service(db, org_id, service_id)
        rows = await db.execute(
            select(MemorialServiceFamily)
            .where(MemorialServiceFamily.service_id == svc.id)
            .order_by(
                MemorialServiceFamily.is_primary.desc(),
                MemorialServiceFamily.created_at,
            )
        )
        return svc, list(rows.scalars().all())

    @staticmethod
    async def list_events(
        db: AsyncSession, org_id: uuid.UUID, service_id: uuid.UUID,
    ) -> list[MemorialServiceEvent]:
        # validate ownership
        await MemorialServicesService.get_service(db, org_id, service_id)
        rows = await db.execute(
            select(MemorialServiceEvent)
            .where(MemorialServiceEvent.service_id == service_id)
            .order_by(MemorialServiceEvent.created_at.desc())
        )
        return list(rows.scalars().all())

    # ------------------------------------------------------------------
    # Create / update
    # ------------------------------------------------------------------
    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialService.consecutive), 0))
            .where(MemorialService.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    async def create_service(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ServiceCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialService:
        consec = await MemorialServicesService._next_consecutive(db, org_id)
        code = f"SVC-{consec:04d}"

        payload = data.model_dump(exclude={"family_members"})
        svc = MemorialService(
            organization_id=org_id,
            consecutive=consec,
            code=code,
            created_by=actor_user_id,
            **payload,
        )
        db.add(svc)
        await db.flush()

        # Family members (al menos 1 marcado como primary)
        has_primary = False
        for fam_data in data.family_members:
            fam = MemorialServiceFamily(
                organization_id=org_id,
                service_id=svc.id,
                **fam_data.model_dump(by_alias=False, exclude={"is_primary"}),
                is_primary=fam_data.is_primary,
            )
            # Workaround: 'relationship' es palabra reservada en SQLAlchemy
            # cuando hay relación con back_populates. La columna en DB es
            # 'relationship'; el modelo la mapea como relationship_.
            fam.relationship_ = fam_data.relationship
            db.add(fam)
            if fam_data.is_primary:
                has_primary = True
        if data.family_members and not has_primary:
            # Primero entra como primario por defecto
            data.family_members[0].is_primary = True
        await db.flush()

        await MemorialServicesService._log_event(
            db, org_id, svc.id, actor_user_id,
            event_type="created",
            body=f"Servicio creado para {_deceased_full_name(svc)}",
        )
        return svc

    @staticmethod
    async def update_service(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        data: ServiceUpdate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialService:
        svc = await MemorialServicesService.get_service(db, org_id, service_id)
        if svc.status in ("finalizado", "cancelado"):
            raise ConflictError(
                "No se puede editar un servicio en estado terminal "
                f"({svc.status}). Reabrir antes de editar.",
            )
        changes = data.model_dump(exclude_unset=True)
        for k, v in changes.items():
            setattr(svc, k, v)
        await db.flush()
        if changes:
            await MemorialServicesService._log_event(
                db, org_id, svc.id, actor_user_id,
                event_type="updated",
                body="Datos del servicio actualizados",
                event_data={"fields": sorted(changes.keys())},
            )
        return svc

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        req: StatusTransitionRequest,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialService:
        from datetime import UTC, datetime as _dt
        svc = await MemorialServicesService.get_service(db, org_id, service_id)
        old = svc.status
        new = req.new_status
        if new == old:
            raise ConflictError(f"El servicio ya está en estado '{old}'.")
        allowed = LEGAL_TRANSITIONS.get(old, set())
        if new not in allowed:
            raise ValidationError(
                f"Transición no permitida: {old} → {new}. "
                f"Estados destino válidos desde '{old}': "
                f"{', '.join(sorted(allowed)) or '(ninguno — estado terminal)'}.",
            )
        svc.status = new
        if new == "finalizado":
            svc.closed_at = _dt.now(UTC)
            svc.closed_by = actor_user_id
        elif new == "cancelado":
            svc.closed_at = _dt.now(UTC)
            svc.closed_by = actor_user_id
        await db.flush()
        await MemorialServicesService._log_event(
            db, org_id, svc.id, actor_user_id,
            event_type="status_changed",
            body=(req.note or f"Estado: {old} → {new}"),
            event_data={"from": old, "to": new},
        )
        return svc

    @staticmethod
    async def add_note(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        data: AddNoteRequest,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialServiceEvent:
        await MemorialServicesService.get_service(db, org_id, service_id)
        return await MemorialServicesService._log_event(
            db, org_id, service_id, actor_user_id,
            event_type="note",
            body=data.body,
        )

    # ------------------------------------------------------------------
    # Family
    # ------------------------------------------------------------------
    @staticmethod
    async def add_family_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        data: FamilyMemberCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialServiceFamily:
        await MemorialServicesService.get_service(db, org_id, service_id)
        if data.is_primary:
            # Quitarle el primary al actual
            await MemorialServicesService._clear_primary(db, org_id, service_id)
        fam = MemorialServiceFamily(
            organization_id=org_id,
            service_id=service_id,
            first_name=data.first_name,
            last_name=data.last_name,
            document_type=data.document_type,
            document_number=data.document_number,
            phone=data.phone,
            mobile=data.mobile,
            email=data.email,
            address=data.address,
            is_primary=data.is_primary,
            notes=data.notes,
        )
        fam.relationship_ = data.relationship
        db.add(fam)
        await db.flush()
        await MemorialServicesService._log_event(
            db, org_id, service_id, actor_user_id,
            event_type="family_added",
            body=f"Familiar añadido: {data.first_name} {data.last_name or ''}".strip(),
        )
        return fam

    @staticmethod
    async def update_family_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        member_id: uuid.UUID,
        data: FamilyMemberUpdate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialServiceFamily:
        fam = await db.scalar(
            select(MemorialServiceFamily).where(
                MemorialServiceFamily.id == member_id,
                MemorialServiceFamily.service_id == service_id,
                MemorialServiceFamily.organization_id == org_id,
            )
        )
        if fam is None:
            raise NotFoundError("Familiar no encontrado en este servicio.")
        changes = data.model_dump(exclude_unset=True)
        if changes.get("is_primary") is True:
            await MemorialServicesService._clear_primary(db, org_id, service_id)
        if "relationship" in changes:
            fam.relationship_ = changes.pop("relationship")
        for k, v in changes.items():
            setattr(fam, k, v)
        await db.flush()
        return fam

    @staticmethod
    async def remove_family_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        member_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
    ) -> None:
        fam = await db.scalar(
            select(MemorialServiceFamily).where(
                MemorialServiceFamily.id == member_id,
                MemorialServiceFamily.service_id == service_id,
                MemorialServiceFamily.organization_id == org_id,
            )
        )
        if fam is None:
            raise NotFoundError("Familiar no encontrado.")
        name = f"{fam.first_name} {fam.last_name or ''}".strip()
        await db.delete(fam)
        await db.flush()
        await MemorialServicesService._log_event(
            db, org_id, service_id, actor_user_id,
            event_type="family_removed",
            body=f"Familiar eliminado: {name}",
        )

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    @staticmethod
    async def dashboard_kpis(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> DashboardKpis:
        rows = await db.execute(
            select(MemorialService.status, func.count(MemorialService.id))
            .where(MemorialService.organization_id == org_id)
            .group_by(MemorialService.status)
        )
        by_status: dict[str, int] = {r[0]: int(r[1]) for r in rows.all()}
        total = sum(by_status.values())
        active = sum(
            v for s, v in by_status.items()
            if s in ("iniciado", "en_proceso", "pendiente")
        )
        closed = by_status.get("finalizado", 0) + by_status.get("cancelado", 0)
        today = date.today()
        today_count = await db.scalar(
            select(func.count(MemorialService.id)).where(
                MemorialService.organization_id == org_id,
                MemorialService.deceased_death_date == today,
            )
        ) or 0
        return DashboardKpis(
            services_total=total,
            services_active=active,
            services_closed=closed,
            services_today=int(today_count),
            services_by_status=by_status,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    async def _clear_primary(
        db: AsyncSession, org_id: uuid.UUID, service_id: uuid.UUID,
    ) -> None:
        rows = await db.execute(
            select(MemorialServiceFamily).where(
                MemorialServiceFamily.service_id == service_id,
                MemorialServiceFamily.organization_id == org_id,
                MemorialServiceFamily.is_primary.is_(True),
            )
        )
        for fam in rows.scalars().all():
            fam.is_primary = False
        await db.flush()

    @staticmethod
    async def _log_event(
        db: AsyncSession,
        org_id: uuid.UUID,
        service_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        *,
        event_type: str,
        body: str,
        event_data: dict[str, Any] | None = None,
    ) -> MemorialServiceEvent:
        ev = MemorialServiceEvent(
            organization_id=org_id,
            service_id=service_id,
            event_type=event_type,
            event_data=event_data,
            body=body,
            actor_user_id=actor_user_id,
        )
        db.add(ev)
        await db.flush()
        return ev
