"""SavvyFlow REST endpoints — /api/v1/automations/*."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.core.exceptions import ForbiddenError
from src.modules.savvy_flow.engine import ACTIONS, CONDITIONS, TRIGGERS
from src.modules.savvy_flow.schemas import (
    CatalogResponse,
    EvaluateResult,
    InstallTemplate,
    NotificationOut,
    RunOut,
    WorkflowCreate,
    WorkflowDetail,
    WorkflowListItem,
    WorkflowUpdate,
)
from src.modules.savvy_flow.service import FlowService
from src.modules.savvy_flow.templates import TEMPLATES

router = APIRouter(prefix="/automations", tags=["SavvyFlow"])


def _uid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


async def _detail(db: AsyncSession, wf) -> dict[str, Any]:
    steps = await FlowService.get_steps(db, wf.id)
    return {
        **{c.name: getattr(wf, c.name) for c in wf.__table__.columns},
        "steps": [
            {"id": s.id, "kind": s.kind, "type": s.type, "config": s.config, "sort_order": s.sort_order}
            for s in steps
        ],
    }


@router.get("/catalog", response_model=CatalogResponse)
async def catalog() -> Any:
    return {"triggers": TRIGGERS, "actions": ACTIONS, "conditions": CONDITIONS, "templates": TEMPLATES}


@router.get("", response_model=list[WorkflowListItem])
async def list_workflows(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.list_(db, org_id)


@router.post("", response_model=WorkflowDetail, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    wf = await FlowService.create(db, org_id, data, created_by=_uid(user))
    return await _detail(db, wf)


@router.post("/install-template", response_model=WorkflowDetail, status_code=status.HTTP_201_CREATED)
async def install_template(
    data: InstallTemplate,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    wf = await FlowService.install_template(db, org_id, data.template_key, created_by=_uid(user))
    return await _detail(db, wf)


@router.post("/evaluate", response_model=EvaluateResult)
async def evaluate_now(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.evaluate(db, org_id)


@router.post("/evaluate-all")
async def evaluate_all(
    x_cron_secret: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Sistema: corre las automatizaciones de datos/agenda de TODAS las orgs.

    Lo invoca un cron externo (Render) con el header X-Cron-Secret. Pensado para
    correr una vez al día. Protegido por secreto compartido (no por JWT).
    """
    secret = get_settings().CRON_SECRET
    if not secret or x_cron_secret != secret:
        raise ForbiddenError("Secreto de cron inválido.")
    orgs = (await db.execute(text("""
        SELECT DISTINCT organization_id FROM automation_workflows
        WHERE is_active = true
          AND trigger_type IN ('schedule_daily','pos_low_stock','memorial_overdue')
    """))).fetchall()
    total = {"orgs": 0, "executed": 0, "skipped": 0}
    for (org_id,) in orgs:
        res = await FlowService.evaluate(db, org_id)
        total["orgs"] += 1
        total["executed"] += res["executed"]
        total["skipped"] += res["skipped"]
    return total


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.notifications(db, org_id)


@router.get("/notifications/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return {"unread": await FlowService.unread_count(db, org_id)}


@router.post("/notifications/read-all")
async def read_all(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    await FlowService.mark_all_read(db, org_id)
    return {"status": "ok"}


@router.get("/{wf_id}", response_model=WorkflowDetail)
async def get_workflow(
    wf_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    wf = await FlowService.get(db, org_id, wf_id)
    return await _detail(db, wf)


@router.patch("/{wf_id}", response_model=WorkflowDetail)
async def update_workflow(
    wf_id: uuid.UUID, data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    wf = await FlowService.update(db, org_id, wf_id, data)
    return await _detail(db, wf)


@router.delete("/{wf_id}")
async def delete_workflow(
    wf_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    await FlowService.delete(db, org_id, wf_id)
    return {"status": "deleted"}


@router.post("/{wf_id}/toggle", response_model=WorkflowListItem)
async def toggle_workflow(
    wf_id: uuid.UUID, active: bool = Query(...),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.toggle(db, org_id, wf_id, active)


@router.post("/{wf_id}/run", response_model=RunOut)
async def run_workflow_now(
    wf_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.run_now(db, org_id, wf_id)


@router.get("/{wf_id}/runs", response_model=list[RunOut])
async def workflow_runs(
    wf_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await FlowService.runs(db, org_id, wf_id)
