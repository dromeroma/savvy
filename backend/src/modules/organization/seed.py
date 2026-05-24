"""Seed data for the business type catalog."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.organization.models import BusinessTypeCatalog

BUSINESS_TYPES = [
    {
        "code": "church",
        "name": "Iglesia",
        "description": "Iglesias, ministerios y organizaciones religiosas",
        "default_app_code": "church",
        "icon": "church",
        "color": "#7C3AED",
        "sort_order": 10,
    },
    {
        "code": "supermarket",
        "name": "Supermercado / Tienda",
        "description": "Supermercados, minimercados y tiendas de retail",
        "default_app_code": "pos",
        "icon": "shopping-cart",
        "color": "#059669",
        "sort_order": 20,
    },
    {
        "code": "restaurant",
        "name": "Restaurante",
        "description": "Restaurantes, cafeterias, bares y comidas rapidas",
        "default_app_code": "pos",
        "icon": "utensils",
        "color": "#EA580C",
        "sort_order": 30,
    },
    {
        "code": "parking",
        "name": "Parqueadero",
        "description": "Parqueaderos, estacionamientos y servicios vehiculares",
        "default_app_code": "parking",
        "icon": "car",
        "color": "#0891B2",
        "sort_order": 40,
    },
    {
        "code": "condo",
        "name": "Conjunto / Condominio",
        "description": "Conjuntos residenciales, condominios y propiedad horizontal",
        "default_app_code": "condo",
        "icon": "building",
        "color": "#DC2626",
        "sort_order": 50,
    },
]


async def seed_business_types(db: AsyncSession) -> None:
    """Seed the business type catalog. Idempotent: skips rows that already exist."""
    for data in BUSINESS_TYPES:
        existing = await db.scalar(
            select(BusinessTypeCatalog).where(BusinessTypeCatalog.code == data["code"])
        )
        if existing is None:
            db.add(BusinessTypeCatalog(**data))
    await db.flush()
