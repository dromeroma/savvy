"""SavvyVision para Parking — lee la placa de una foto y sugiere la acción.

Usa Claude Vision (vía savvy_ai) para extraer la placa + estado del vehículo,
luego consulta parking para saber si tiene sesión abierta y sugiere entrada,
salida o lavado. La llamada al LLM se mide en ai_usage.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_ai.client import get_provider
from src.modules.savvy_ai.prompts.registry import get_prompt
from src.modules.savvy_ai.usage import CallContext, check_quota, record_usage
from src.modules.savvy_ai.vision import extract_document


async def scan_plate(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Lee la placa y devuelve una sugerencia de acción para el operador."""
    await check_quota(db, org_id)
    spec = get_prompt("extraction.vehicle_plate")
    provider = await get_provider(db)
    out = await extract_document(
        provider, spec,
        file_bytes=file_bytes, filename=filename, content_type=content_type,
    )
    await record_usage(
        db,
        CallContext(
            organization_id=org_id, user_id=user_id, app_code="parking",
            feature="vision", action="parking.scan_plate",
            prompt_key=spec.key, prompt_version=spec.version, tier=spec.tier,
        ),
        out.result,
    )
    await db.commit()

    data = out.data or {}
    plate = (data.get("plate") or "").strip().upper().replace(" ", "")
    looks_dirty = bool(data.get("looks_dirty"))

    result: dict[str, Any] = {
        "plate": plate or None,
        "vehicle_type": data.get("vehicle_type"),
        "color": data.get("color"),
        "brand": data.get("brand"),
        "looks_dirty": looks_dirty,
        "plate_confidence": data.get("plate_confidence"),
        "known_vehicle": None,
        "open_session": None,
        "suggested_action": "manual",
        "suggestion_text": "No se pudo leer la placa. Ingrésala manualmente.",
        "wash_suggestion": None,
    }
    if not plate:
        return result

    # ¿Vehículo conocido?
    veh = (await db.execute(text("""
        SELECT id::text AS id, brand, model, color, vehicle_type
        FROM parking_vehicles
        WHERE organization_id = :org AND upper(replace(plate,' ','')) = :plate
        LIMIT 1
    """), {"org": org_id, "plate": plate})).mappings().first()
    result["known_vehicle"] = dict(veh) if veh else None

    # ¿Sesión abierta?
    sess = (await db.execute(text("""
        SELECT id::text AS id, entry_time, location_id::text AS location_id
        FROM parking_sessions
        WHERE organization_id = :org AND upper(replace(plate,' ','')) = :plate
          AND status = 'active' AND exit_time IS NULL
        ORDER BY entry_time DESC LIMIT 1
    """), {"org": org_id, "plate": plate})).mappings().first()

    if sess:
        result["open_session"] = dict(sess)
        result["suggested_action"] = "exit"
        result["suggestion_text"] = f"El vehículo {plate} está dentro. ¿Registrar SALIDA?"
    else:
        result["suggested_action"] = "entry"
        known = " (cliente conocido)" if veh else ""
        result["suggestion_text"] = f"El vehículo {plate}{known} no está dentro. ¿Registrar ENTRADA?"

    # ¿Sugerir lavado?
    if looks_dirty:
        wash = (await db.execute(text("""
            SELECT id::text AS id, name, price FROM parking_services
            WHERE organization_id = :org AND status = 'active'
              AND (lower(name) LIKE '%lav%' OR lower(category) LIKE '%lav%' OR lower(category) LIKE '%wash%')
            ORDER BY price LIMIT 1
        """), {"org": org_id})).mappings().first()
        result["wash_suggestion"] = {
            "looks_dirty": True,
            "service": dict(wash) if wash else None,
            "text": (
                f"El vehículo se ve sucio. ¿Ofrecer «{wash['name']}»"
                + (f" (${float(wash['price']):,.0f})" if wash and wash.get("price") else "")
                + "?"
            ) if wash else "El vehículo se ve sucio. ¿Ofrecer servicio de lavado?",
        }
    return result
