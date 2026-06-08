"""SavvyAI REST endpoints.

Dos superficies:
  - /api/v1/ai/*           → organización (usuarios con la app de IA)
  - /api/v1/platform/ai/*  → super admin (API key + uso global)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.core.exceptions import ValidationError
from src.modules.platform.dependencies import require_super_admin
from src.modules.savvy_ai.client import AiNotConfiguredError
from src.modules.savvy_ai.schemas import (
    AiOrgSettingsResponse,
    BriefingResponse,
    ConfirmableAction,
    CopilotRequest,
    CopilotResponse,
    ExtractionConfirm,
    ExtractionField,
    OrgUsageReport,
    PlatformUsageReport,
    ProviderConfigResponse,
    ProviderConfigUpdate,
    ProviderTestResult,
    UniversalSearchResponse,
    WhatsappTestRequest,
)
from src.modules.savvy_ai.service import (
    ProviderService,
    ScanService,
    UsageAnalyticsService,
)
from src.modules.savvy_ai.usage import QuotaExceededError, get_or_create_settings

# ============================================================ Org router

router = APIRouter(prefix="/ai", tags=["SavvyAI"])


def _uid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


def _to_confirmable(ext, apply_result: dict[str, Any] | None = None) -> ConfirmableAction:
    data = ext.extracted_data or {}
    fc = ext.field_confidence or {}
    skip = {"line_items", "field_confidence"}
    fields = [
        ExtractionField(
            key=k, label=k.replace("_", " ").capitalize(), value=v,
            confidence=fc.get(k), editable=True,
        )
        for k, v in data.items() if k not in skip
    ]
    items = data.get("line_items", []) if isinstance(data, dict) else []
    n = len(items)
    total = data.get("total") if isinstance(data, dict) else None
    summary = f"{n} ítem(s)" + (f" · total {total}" if total else "")
    return ConfirmableAction(
        extraction_id=ext.id,
        title=f"Revisar {ext.document_type.replace('_', ' ')}",
        target_app=ext.target_app,
        document_type=ext.document_type,
        summary=summary,
        confidence=float(ext.confidence) if ext.confidence is not None else None,
        fields=fields,
        line_items=items,
        status=ext.status,
        result_summary=apply_result.get("summary") if apply_result else None,
        result=apply_result,
    )


@router.post("/scan", response_model=ConfirmableAction)
async def scan_document(
    file: UploadFile = File(...),
    prompt_key: str = Form("extraction.purchase_invoice"),
    target_app: str = Form("pos"),
    document_type: str = Form("purchase_invoice"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    from src.core.uploads import read_limited
    file_bytes = await read_limited(file)
    try:
        ext = await ScanService.scan_document(
            db, org_id,
            prompt_key=prompt_key, target_app=target_app, document_type=document_type,
            file_bytes=file_bytes, filename=file.filename or "documento",
            content_type=file.content_type, user_id=_uid(user),
        )
    except AiNotConfiguredError as exc:
        raise ValidationError(str(exc))
    except QuotaExceededError as exc:
        raise ValidationError(str(exc))
    return _to_confirmable(ext)


@router.get("/extractions/{eid}", response_model=ConfirmableAction)
async def get_extraction(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return _to_confirmable(await ScanService.get_extraction(db, org_id, eid))


@router.post("/extractions/{eid}/confirm", response_model=ConfirmableAction)
async def confirm_extraction(
    eid: uuid.UUID,
    data: ExtractionConfirm,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    ext, apply_result = await ScanService.confirm(
        db, org_id, eid, edited_data=data.edited_data, user_id=_uid(user),
    )
    return _to_confirmable(ext, apply_result)


@router.post("/extractions/{eid}/discard")
async def discard_extraction(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    await ScanService.discard(db, org_id, eid, user_id=_uid(user))
    return {"status": "discarded"}


@router.get("/usage", response_model=OrgUsageReport)
async def org_usage(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await UsageAnalyticsService.org_report(db, org_id)


@router.get("/settings", response_model=AiOrgSettingsResponse)
async def org_ai_settings(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await get_or_create_settings(db, org_id)


# ---------- Fase 2: Búsqueda universal (Savvy Graph) ----------

@router.get("/search", response_model=UniversalSearchResponse)
async def universal_search_endpoint(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from src.modules.savvy_ai.graph import resolve_person, universal_search
    hits = await universal_search(db, org_id, q)
    people = await resolve_person(db, org_id, q)
    return {
        "query": q,
        "hits": [h.__dict__ for h in hits],
        "people": [
            {"display_name": p.display_name, "document_number": p.document_number,
             "hits": [h.__dict__ for h in p.hits]}
            for p in people
        ],
    }


# ---------- Fase 2: Copilot ----------

@router.post("/copilot", response_model=CopilotResponse)
async def copilot_ask(
    data: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    from src.modules.savvy_ai.copilot import ask
    try:
        result = await ask(db, org_id, data.message, user_id=_uid(user))
    except AiNotConfiguredError as exc:
        raise ValidationError(str(exc))
    except QuotaExceededError as exc:
        raise ValidationError(str(exc))
    return {"answer": result.answer, "tools_used": result.tools_used}


# ---------- Fase 2: Briefing ----------

@router.get("/briefing", response_model=BriefingResponse)
async def daily_briefing(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    from src.modules.savvy_ai.briefing import generate
    return await generate(db, org_id, user_id=_uid(user))


# ---------- Fase 3: Insights predictivos + recomendaciones ----------

@router.get("/insights/summary")
async def insights_summary_endpoint(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from src.modules.savvy_ai.insights import insights_summary
    return await insights_summary(db, org_id)


@router.get("/insights/pos")
async def insights_pos(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from src.modules.savvy_ai.insights import (
        pos_inventory_insights, pos_promo_recommendations,
    )
    inv = await pos_inventory_insights(db, org_id)
    promos = await pos_promo_recommendations(db, org_id)
    return {**inv, **promos}


@router.get("/insights/memorial")
async def insights_memorial(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from src.modules.savvy_ai.insights import memorial_collection_risk
    return await memorial_collection_risk(db, org_id)


# ============================================================ Platform router

platform_router = APIRouter(prefix="/platform/ai", tags=["SavvyAI · Plataforma"])


@platform_router.get("/provider", response_model=ProviderConfigResponse)
async def get_provider_config(
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    cfg = await ProviderService.get(db)
    return ProviderService.to_response(cfg)


@platform_router.patch("/provider", response_model=ProviderConfigResponse)
async def update_provider_config(
    data: ProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    cfg = await ProviderService.update(
        db, data.model_dump(exclude_unset=True), actor=_uid(user),
    )
    return ProviderService.to_response(cfg)


@platform_router.post("/provider/test", response_model=ProviderTestResult)
async def test_provider(
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    try:
        return await ProviderService.test_connection(db)
    except AiNotConfiguredError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": f"Error: {str(exc)[:300]}"}


@platform_router.post("/whatsapp/test")
async def whatsapp_test(
    data: WhatsappTestRequest,
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    from src.modules.savvy_ai.whatsapp import send_whatsapp
    return await send_whatsapp(db, data.to, data.message)


@platform_router.get("/usage", response_model=PlatformUsageReport)
async def platform_usage(
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    return await UsageAnalyticsService.platform_report(db)


@platform_router.get("/usage/{org_id}", response_model=OrgUsageReport)
async def platform_org_usage(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_super_admin),
) -> Any:
    return await UsageAnalyticsService.org_report(db, org_id)
