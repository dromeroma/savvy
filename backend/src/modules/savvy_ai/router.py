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
    ConfirmableAction,
    ExtractionConfirm,
    ExtractionField,
    OrgUsageReport,
    PlatformUsageReport,
    ProviderConfigResponse,
    ProviderConfigUpdate,
    ProviderTestResult,
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
    file_bytes = await file.read()
    if not file_bytes:
        raise ValidationError("Archivo vacío.")
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
