"""Envío de WhatsApp vía Meta Cloud API.

El token se lee CIFRADO de ai_provider_config (lo configura el super admin).
Si no está configurado, devuelve un resultado "no enviado" sin romper —
las acciones de SavvyFlow lo registran como pendiente.
"""

from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_ai.crypto import decrypt_secret
from src.modules.savvy_ai.models import AiProviderConfig

GRAPH_URL = "https://graph.facebook.com/v21.0"


async def whatsapp_status(db: AsyncSession) -> dict:
    cfg = (await db.execute(select(AiProviderConfig).limit(1))).scalar_one_or_none()
    enabled = bool(cfg and cfg.whatsapp_enabled and cfg.whatsapp_token_encrypted and cfg.whatsapp_phone_id)
    return {
        "enabled": enabled,
        "phone_id": cfg.whatsapp_phone_id if cfg else None,
        "has_token": bool(cfg and cfg.whatsapp_token_encrypted),
    }


async def send_whatsapp(db: AsyncSession, to: str, message: str) -> dict:
    """Envía un texto por WhatsApp. Devuelve {ok, ...}.

    No lanza si no está configurado — devuelve ok=False con pending=True para que
    SavvyFlow lo registre como "se enviará cuando se active".
    """
    cfg = (await db.execute(select(AiProviderConfig).limit(1))).scalar_one_or_none()
    if not (cfg and cfg.whatsapp_enabled and cfg.whatsapp_token_encrypted and cfg.whatsapp_phone_id):
        return {"ok": False, "pending": True, "reason": "WhatsApp no configurado/activado."}
    token = decrypt_secret(cfg.whatsapp_token_encrypted)
    if not token:
        return {"ok": False, "pending": True, "reason": "Token de WhatsApp no se pudo descifrar."}
    if not to:
        return {"ok": False, "reason": "Destinatario vacío."}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message[:4096]},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{GRAPH_URL}/{cfg.whatsapp_phone_id}/messages"
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            resp = await http.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            return {"ok": False, "status": resp.status_code, "error": resp.text[:300]}
        data = resp.json()
        msg_id = (data.get("messages") or [{}])[0].get("id")
        return {"ok": True, "message_id": msg_id}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:300]}
