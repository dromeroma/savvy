"""Seed data for the app registry."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.apps.models import AppRegistry

DEFAULT_APPS = [
    {
        "code": "church",
        "name": "SavvyChurch",
        "description": "Gestión integral de iglesias: miembros, finanzas, contabilidad y reportes",
        "icon": "church",
        "color": "#7C3AED",
    },
    {
        "code": "pos",
        "name": "SavvyPOS",
        "description": "Sistema punto de venta: productos, ventas, inventario",
        "icon": "store",
        "color": "#059669",
    },
    {
        "code": "accounting",
        "name": "SavvyAccounting",
        "description": "Contabilidad avanzada: reportes financieros, impuestos, auditoría",
        "icon": "calculator",
        "color": "#2563EB",
    },
]

# Default roles per app
APP_DEFAULT_ROLES: dict[str, list[str]] = {
    "church": ["pastor", "contador", "lider", "miembro"],
    "pos": ["gerente", "cajero", "bodeguero"],
    "accounting": ["contador", "auditor"],
}

# Role assigned to the user who activates the app
APP_OWNER_ROLE: dict[str, str] = {
    "church": "pastor",
    "pos": "gerente",
    "accounting": "contador",
}


async def seed_apps(db: AsyncSession) -> None:
    """Seed default apps into app_registry."""
    for app_data in DEFAULT_APPS:
        existing = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_data["code"])
        )
        if existing is None:
            db.add(AppRegistry(**app_data))
    await db.flush()
