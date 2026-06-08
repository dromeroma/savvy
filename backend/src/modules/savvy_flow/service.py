"""SavvyFlow · service (CRUD de flujos + ejecución + bandeja)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.modules.savvy_flow.engine import run_workflow
from src.modules.savvy_flow.models import (
    AutomationNotification,
    AutomationRun,
    AutomationStep,
    AutomationWorkflow,
)
from src.modules.savvy_flow.schemas import StepIn, WorkflowCreate, WorkflowUpdate
from src.modules.savvy_flow.templates import get_template


def _now() -> datetime:
    return datetime.now(UTC)


class FlowService:

    @staticmethod
    async def list_(db: AsyncSession, org_id: uuid.UUID) -> list[AutomationWorkflow]:
        rows = await db.execute(
            select(AutomationWorkflow)
            .where(AutomationWorkflow.organization_id == org_id)
            .order_by(AutomationWorkflow.created_at.desc())
        )
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID) -> AutomationWorkflow:
        wf = (await db.execute(
            select(AutomationWorkflow).where(
                AutomationWorkflow.id == wf_id,
                AutomationWorkflow.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if wf is None:
            raise NotFoundError("Automatización no encontrada")
        return wf

    @staticmethod
    async def get_steps(db: AsyncSession, wf_id: uuid.UUID) -> list[AutomationStep]:
        rows = await db.execute(
            select(AutomationStep)
            .where(AutomationStep.workflow_id == wf_id)
            .order_by(AutomationStep.sort_order)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def _replace_steps(
        db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID, steps: list[StepIn],
    ) -> None:
        await db.execute(delete(AutomationStep).where(AutomationStep.workflow_id == wf_id))
        for i, s in enumerate(steps):
            db.add(AutomationStep(
                organization_id=org_id, workflow_id=wf_id,
                sort_order=s.sort_order or i, kind=s.kind, type=s.type, config=s.config or {},
            ))

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: WorkflowCreate, *, created_by: uuid.UUID | None,
    ) -> AutomationWorkflow:
        wf = AutomationWorkflow(
            organization_id=org_id, name=data.name, description=data.description,
            trigger_type=data.trigger_type, trigger_config=data.trigger_config or {},
            is_active=data.is_active, created_by=created_by,
        )
        db.add(wf)
        await db.flush()
        await FlowService._replace_steps(db, org_id, wf.id, data.steps)
        await db.commit()
        await db.refresh(wf)
        return wf

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID, data: WorkflowUpdate,
    ) -> AutomationWorkflow:
        wf = await FlowService.get(db, org_id, wf_id)
        for k in ("name", "description", "trigger_type", "trigger_config", "is_active"):
            v = getattr(data, k)
            if v is not None:
                setattr(wf, k, v)
        if data.steps is not None:
            await FlowService._replace_steps(db, org_id, wf_id, data.steps)
        wf.updated_at = _now()
        await db.commit()
        await db.refresh(wf)
        return wf

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID) -> None:
        wf = await FlowService.get(db, org_id, wf_id)
        await db.delete(wf)
        await db.commit()

    @staticmethod
    async def toggle(db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID, active: bool) -> AutomationWorkflow:
        wf = await FlowService.get(db, org_id, wf_id)
        wf.is_active = active
        wf.updated_at = _now()
        await db.commit()
        await db.refresh(wf)
        return wf

    @staticmethod
    async def run_now(db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID) -> AutomationRun:
        wf = await FlowService.get(db, org_id, wf_id)
        steps = await FlowService.get_steps(db, wf_id)
        run = await run_workflow(db, org_id, wf, steps, source="manual")
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def evaluate(db: AsyncSession, org_id: uuid.UUID) -> dict[str, int]:
        """Corre todos los flujos activos con trigger de datos/agenda.

        Pensado para un cron diario o un botón "evaluar ahora". Omite los que
        no tienen items (no spamea).
        """
        wfs = (await db.execute(
            select(AutomationWorkflow).where(
                AutomationWorkflow.organization_id == org_id,
                AutomationWorkflow.is_active.is_(True),
                AutomationWorkflow.trigger_type.in_(
                    ["schedule_daily", "pos_low_stock", "memorial_overdue"]
                ),
            )
        )).scalars().all()
        executed = skipped = 0
        for wf in wfs:
            steps = await FlowService.get_steps(db, wf.id)
            run = await run_workflow(db, org_id, wf, steps, source="evaluate", only_if_matches=True)
            if run.status == "skipped":
                skipped += 1
            else:
                executed += 1
        await db.commit()
        return {"evaluated": len(wfs), "executed": executed, "skipped": skipped}

    @staticmethod
    async def install_template(
        db: AsyncSession, org_id: uuid.UUID, key: str, *, created_by: uuid.UUID | None,
    ) -> AutomationWorkflow:
        tpl = get_template(key)
        if tpl is None:
            raise NotFoundError("Plantilla no encontrada")
        data = WorkflowCreate(
            name=tpl["name"], description=tpl["description"],
            trigger_type=tpl["trigger_type"], trigger_config=tpl.get("trigger_config", {}),
            is_active=True,
            steps=[StepIn(kind=s["kind"], type=s["type"], config=s.get("config", {}), sort_order=i)
                   for i, s in enumerate(tpl["steps"])],
        )
        return await FlowService.create(db, org_id, data, created_by=created_by)

    @staticmethod
    async def runs(db: AsyncSession, org_id: uuid.UUID, wf_id: uuid.UUID, limit: int = 20) -> list[AutomationRun]:
        rows = await db.execute(
            select(AutomationRun)
            .where(AutomationRun.workflow_id == wf_id, AutomationRun.organization_id == org_id)
            .order_by(AutomationRun.started_at.desc()).limit(limit)
        )
        return list(rows.scalars().all())

    # -------- Bandeja (notificaciones de SavvyFlow) --------

    @staticmethod
    async def notifications(db: AsyncSession, org_id: uuid.UUID, limit: int = 50) -> list[AutomationNotification]:
        rows = await db.execute(
            select(AutomationNotification)
            .where(AutomationNotification.organization_id == org_id)
            .order_by(AutomationNotification.created_at.desc()).limit(limit)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def unread_count(db: AsyncSession, org_id: uuid.UUID) -> int:
        return (await db.execute(
            select(func.count(AutomationNotification.id)).where(
                AutomationNotification.organization_id == org_id,
                AutomationNotification.read_at.is_(None),
            )
        )).scalar() or 0

    @staticmethod
    async def mark_all_read(db: AsyncSession, org_id: uuid.UUID) -> None:
        await db.execute(
            update(AutomationNotification)
            .where(AutomationNotification.organization_id == org_id,
                   AutomationNotification.read_at.is_(None))
            .values(read_at=_now())
        )
        await db.commit()
