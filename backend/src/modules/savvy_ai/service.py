"""SavvyAI · orquestación: provider config, scan, confirm, analítica de uso."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.modules.organization.models import Organization
from src.modules.savvy_ai.client import ClaudeProvider, get_provider
from src.modules.savvy_ai.crypto import encrypt_secret, key_hint
from src.modules.savvy_ai.models import (
    AiAuditLog,
    AiExtraction,
    AiJob,
    AiOrgSettings,
    AiProviderConfig,
    AiUsage,
)
from src.modules.savvy_ai.prompts.registry import get_prompt
from src.modules.savvy_ai.usage import CallContext, check_quota, record_usage
from src.modules.savvy_ai.vision import extract_document


def _now() -> datetime:
    return datetime.now(UTC)


async def _apply_to_target_app(
    db: AsyncSession, org_id: uuid.UUID, ext: AiExtraction, user_id: uuid.UUID | None,
) -> dict[str, Any] | None:
    """Aplica una extracción confirmada a la app destino.

    Import perezoso para evitar dependencias circulares con las apps. Cada
    (target_app, document_type) tiene su aplicador. Si no hay aplicador,
    la confirmación solo marca el estado (sin efecto en otra app).
    """
    target = (ext.target_app or "").lower()
    doc = (ext.document_type or "").lower()

    if target == "pos" and doc == "purchase_invoice":
        from src.apps.pos.ai_apply import apply_purchase_invoice
        result = await apply_purchase_invoice(db, org_id, ext.extracted_data or {}, user_id=user_id)
        c, u = result["products_created"], result["products_updated"]
        return {
            "entity_type": "pos_purchase",
            "summary": (
                f"Inventario actualizado: {c} producto(s) creado(s), {u} actualizado(s), "
                f"{result['total_units']:.0f} unidades en '{result['location']}'."
            ),
            **result,
        }
    return None


# ============================================================ Provider (super admin)


class ProviderService:

    @staticmethod
    async def get(db: AsyncSession) -> AiProviderConfig:
        cfg = (await db.execute(select(AiProviderConfig).limit(1))).scalar_one_or_none()
        if cfg is None:
            cfg = AiProviderConfig(provider="anthropic", is_enabled=False)
            db.add(cfg)
            await db.flush()
            await db.commit()
        return cfg

    @staticmethod
    async def update(
        db: AsyncSession, data: dict[str, Any], *, actor: uuid.UUID | None,
    ) -> AiProviderConfig:
        cfg = await ProviderService.get(db)
        api_key = data.pop("api_key", None)
        if api_key:
            cfg.api_key_encrypted = encrypt_secret(api_key)
            cfg.api_key_hint = key_hint(api_key)
        wa_token = data.pop("whatsapp_token", None)
        if wa_token:
            cfg.whatsapp_token_encrypted = encrypt_secret(wa_token)
            cfg.whatsapp_token_hint = key_hint(wa_token)
        for k, v in data.items():
            if v is not None and hasattr(cfg, k):
                setattr(cfg, k, v)
        cfg.updated_by = actor
        cfg.updated_at = _now()
        await db.commit()
        await db.refresh(cfg)
        return cfg

    @staticmethod
    def to_response(cfg: AiProviderConfig) -> dict[str, Any]:
        return {
            "id": cfg.id,
            "provider": cfg.provider,
            "is_enabled": cfg.is_enabled,
            "has_api_key": bool(cfg.api_key_encrypted),
            "api_key_hint": cfg.api_key_hint,
            "model_haiku": cfg.model_haiku,
            "model_sonnet": cfg.model_sonnet,
            "model_opus": cfg.model_opus,
            "default_tier": cfg.default_tier,
            "pricing": cfg.pricing or {},
            "whatsapp_enabled": cfg.whatsapp_enabled,
            "has_whatsapp_token": bool(cfg.whatsapp_token_encrypted),
            "whatsapp_token_hint": cfg.whatsapp_token_hint,
            "whatsapp_phone_id": cfg.whatsapp_phone_id,
            "updated_at": cfg.updated_at,
        }

    @staticmethod
    async def test_connection(db: AsyncSession) -> dict[str, Any]:
        """Hace un ping mínimo al modelo para validar la API key."""
        provider = await get_provider(db)
        result = await provider.complete(
            messages=[{"role": "user", "content": "Responde solo: OK"}],
            tier="haiku",
            max_tokens=8,
        )
        return {
            "ok": True,
            "message": "Conexión exitosa con el proveedor de IA.",
            "model": result.model,
            "latency_ms": result.latency_ms,
        }


# ============================================================ Scan (SavvyScan)


class ScanService:

    @staticmethod
    async def scan_document(
        db: AsyncSession,
        org_id: uuid.UUID,
        *,
        prompt_key: str,
        target_app: str,
        document_type: str,
        file_bytes: bytes,
        filename: str,
        content_type: str | None,
        user_id: uuid.UUID | None,
    ) -> AiExtraction:
        await check_quota(db, org_id)
        spec = get_prompt(prompt_key)

        job = AiJob(
            organization_id=org_id, job_type="scan", status="running",
            source_kind="file", source_ref=filename, app_code=target_app,
            action=prompt_key, created_by=user_id, input_summary=f"Scan {document_type}",
        )
        db.add(job)
        await db.flush()

        provider: ClaudeProvider = await get_provider(db)
        try:
            out = await extract_document(
                provider, spec,
                file_bytes=file_bytes, filename=filename, content_type=content_type,
            )
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)[:1000]
            job.completed_at = _now()
            db.add(AiAuditLog(
                organization_id=org_id, job_id=job.id, action="error",
                actor_user_id=user_id, app_code=target_app,
                summary=f"Falló extracción de {document_type}", payload={"error": str(exc)[:500]},
            ))
            await db.commit()
            raise

        # Medir uso (SIEMPRE)
        await record_usage(
            db,
            CallContext(
                organization_id=org_id, user_id=user_id, app_code=target_app,
                feature="scan", action=prompt_key,
                prompt_key=spec.key, prompt_version=spec.version,
                tier=spec.tier, job_id=job.id,
            ),
            out.result,
        )

        job.status = "succeeded"
        job.model_used = out.result.model
        job.latency_ms = out.result.latency_ms
        job.output = out.data
        job.completed_at = _now()

        extraction = AiExtraction(
            organization_id=org_id, job_id=job.id, document_type=document_type,
            target_app=target_app, extracted_data=out.data,
            confidence=Decimal(str(out.confidence)) if out.confidence is not None else None,
            field_confidence=out.field_confidence, status="pending_review",
        )
        db.add(extraction)
        await db.flush()
        db.add(AiAuditLog(
            organization_id=org_id, job_id=job.id, extraction_id=extraction.id,
            action="proposed", actor_user_id=user_id, app_code=target_app,
            summary=f"IA propuso datos de {document_type}",
        ))
        await db.commit()
        await db.refresh(extraction)
        return extraction

    @staticmethod
    async def get_extraction(db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID) -> AiExtraction:
        row = (await db.execute(
            select(AiExtraction).where(
                AiExtraction.id == eid, AiExtraction.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Extracción no encontrada")
        return row

    @staticmethod
    async def confirm(
        db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID,
        *, edited_data: dict | None, user_id: uuid.UUID | None,
    ) -> tuple[AiExtraction, dict[str, Any] | None]:
        ext = await ScanService.get_extraction(db, org_id, eid)
        if ext.status == "confirmed":
            return ext, None  # idempotente: no re-aplicar al inventario
        if edited_data is not None:
            ext.extracted_data = edited_data
        ext.status = "confirmed"
        ext.confirmed_by = user_id
        ext.updated_at = _now()

        # Dispatch a la app destino: aplica la extracción a entidades reales.
        apply_result = await _apply_to_target_app(db, org_id, ext, user_id)
        if apply_result:
            ext.confirmed_entity_type = apply_result.get("entity_type")

        db.add(AiAuditLog(
            organization_id=org_id, extraction_id=ext.id,
            action="edited" if edited_data is not None else "confirmed",
            actor_user_id=user_id, app_code=ext.target_app,
            summary=apply_result.get("summary") if apply_result
            else f"Usuario confirmó datos de {ext.document_type}",
            payload={"extracted": ext.extracted_data, "applied": apply_result},
        ))
        await db.commit()
        await db.refresh(ext)
        return ext, apply_result

    @staticmethod
    async def discard(
        db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID, *, user_id: uuid.UUID | None,
    ) -> None:
        ext = await ScanService.get_extraction(db, org_id, eid)
        ext.status = "discarded"
        ext.updated_at = _now()
        db.add(AiAuditLog(
            organization_id=org_id, extraction_id=ext.id, action="discarded",
            actor_user_id=user_id, app_code=ext.target_app,
            summary=f"Usuario descartó extracción de {ext.document_type}",
        ))
        await db.commit()


# ============================================================ Analítica de uso


class UsageAnalyticsService:

    @staticmethod
    async def _breakdown(db, org_id, column, label_map=None, limit=10):
        rows = (await db.execute(
            select(
                column.label("key"),
                func.count(AiUsage.id).label("calls"),
                func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AiUsage.cost_usd), 0).label("cost"),
            )
            .where(AiUsage.organization_id == org_id)
            .group_by(column)
            .order_by(func.sum(AiUsage.cost_usd).desc())
            .limit(limit)
        )).all()
        out = []
        for r in rows:
            key = r.key or "—"
            out.append({
                "key": str(key),
                "label": (label_map or {}).get(key, str(key)),
                "calls": int(r.calls),
                "tokens": int(r.tokens),
                "cost_usd": Decimal(r.cost or 0),
            })
        return out

    @staticmethod
    async def org_report(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
        totals = (await db.execute(
            select(
                func.coalesce(func.sum(AiUsage.cost_usd), 0),
                func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0),
                func.count(AiUsage.id),
            ).where(AiUsage.organization_id == org_id)
        )).one()
        settings = (await db.execute(
            select(AiOrgSettings).where(AiOrgSettings.organization_id == org_id)
        )).scalar_one_or_none()

        # user labels
        from src.modules.auth.models import User
        user_rows = (await db.execute(select(User.id, User.name, User.email))).all()
        user_labels = {u.id: (u.name or u.email or str(u.id)) for u in user_rows}

        return {
            "organization_id": org_id,
            "summary": {
                "total_cost_usd": Decimal(totals[0] or 0),
                "total_tokens": int(totals[1] or 0),
                "total_calls": int(totals[2] or 0),
                "quota": settings.monthly_token_quota if settings else 0,
                "tokens_used_this_period": settings.tokens_used_this_period if settings else 0,
            },
            "by_app": await UsageAnalyticsService._breakdown(db, org_id, AiUsage.app_code),
            "by_action": await UsageAnalyticsService._breakdown(db, org_id, AiUsage.action),
            "by_user": await UsageAnalyticsService._breakdown(db, org_id, AiUsage.user_id, user_labels),
            "by_prompt": await UsageAnalyticsService._breakdown(db, org_id, AiUsage.prompt_key),
        }

    @staticmethod
    async def platform_report(db: AsyncSession) -> dict[str, Any]:
        totals = (await db.execute(
            select(
                func.coalesce(func.sum(AiUsage.cost_usd), 0),
                func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0),
                func.count(AiUsage.id),
                func.count(func.distinct(AiUsage.organization_id)),
            )
        )).one()

        by_org_rows = (await db.execute(
            select(
                AiUsage.organization_id,
                Organization.name,
                func.count(AiUsage.id),
                func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0),
                func.coalesce(func.sum(AiUsage.cost_usd), 0),
            )
            .join(Organization, Organization.id == AiUsage.organization_id)
            .group_by(AiUsage.organization_id, Organization.name)
            .order_by(func.sum(AiUsage.cost_usd).desc())
        )).all()

        def _model_app_breakdown(column):
            return (
                select(
                    column.label("key"),
                    func.count(AiUsage.id).label("calls"),
                    func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0).label("tokens"),
                    func.coalesce(func.sum(AiUsage.cost_usd), 0).label("cost"),
                )
                .group_by(column)
                .order_by(func.sum(AiUsage.cost_usd).desc())
            )

        model_rows = (await db.execute(_model_app_breakdown(AiUsage.model))).all()
        app_rows = (await db.execute(_model_app_breakdown(AiUsage.app_code))).all()

        return {
            "total_cost_usd": Decimal(totals[0] or 0),
            "total_tokens": int(totals[1] or 0),
            "total_calls": int(totals[2] or 0),
            "active_orgs": int(totals[3] or 0),
            "by_organization": [
                {
                    "organization_id": r[0], "organization_name": r[1],
                    "calls": int(r[2]), "tokens": int(r[3]), "cost_usd": Decimal(r[4] or 0),
                } for r in by_org_rows
            ],
            "by_model": [
                {"key": str(r.key or "—"), "label": str(r.key or "—"),
                 "calls": int(r.calls), "tokens": int(r.tokens), "cost_usd": Decimal(r.cost or 0)}
                for r in model_rows
            ],
            "by_app": [
                {"key": str(r.key or "—"), "label": str(r.key or "—"),
                 "calls": int(r.calls), "tokens": int(r.tokens), "cost_usd": Decimal(r.cost or 0)}
                for r in app_rows
            ],
        }
