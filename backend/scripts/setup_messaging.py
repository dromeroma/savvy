"""DDL idempotente — config de WhatsApp (Fase 4) sobre ai_provider_config.

Agrega columnas para la integración de WhatsApp Cloud API (Meta). El token se
guarda cifrado. Se administra desde el panel del super admin.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402


DDL = [
    "ALTER TABLE ai_provider_config ADD COLUMN IF NOT EXISTS whatsapp_enabled BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE ai_provider_config ADD COLUMN IF NOT EXISTS whatsapp_token_encrypted TEXT",
    "ALTER TABLE ai_provider_config ADD COLUMN IF NOT EXISTS whatsapp_token_hint VARCHAR(20)",
    "ALTER TABLE ai_provider_config ADD COLUMN IF NOT EXISTS whatsapp_phone_id VARCHAR(60)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyAI · setup config WhatsApp (Fase 4)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, 1):
            print(f"  [{i}/{len(DDL)}] {stmt[:80]}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — columnas WhatsApp listas.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
