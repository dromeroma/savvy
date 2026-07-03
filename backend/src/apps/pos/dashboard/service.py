"""SavvyPOS dashboard KPIs."""

from __future__ import annotations
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.pos.sales.models import PosSale
from src.apps.pos.catalog.models import PosProduct
from src.apps.pos.inventory.models import PosInventory
from src.core.timezone import APP_TZ_NAME, local_today


class PosDashboardService:

    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        today = local_today()  # fecha local (Colombia), no UTC del servidor
        today_sales = await db.execute(select(
            func.count().label("count"),
            func.coalesce(func.sum(PosSale.total), 0).label("revenue"),
        ).where(
            PosSale.organization_id == org_id,
            PosSale.status == "completed",
            # convierte el timestamptz a Colombia antes de tomar la fecha
            func.date(func.timezone(APP_TZ_NAME, PosSale.created_at)) == today,
        ))
        t = today_sales.one()

        total_sales = await db.execute(select(
            func.count().label("count"),
            func.coalesce(func.sum(PosSale.total), 0).label("revenue"),
        ).where(PosSale.organization_id == org_id, PosSale.status == "completed"))
        s = total_sales.one()

        products = await db.execute(select(func.count()).where(PosProduct.organization_id == org_id, PosProduct.status == "active"))
        low_stock = await db.execute(select(func.count()).where(
            PosInventory.organization_id == org_id,
            PosInventory.quantity <= PosInventory.min_stock,
        ))

        return {
            "today_sales": t.count, "today_revenue": float(t.revenue),
            "total_sales": s.count, "total_revenue": float(s.revenue),
            "active_products": products.scalar() or 0,
            "low_stock_items": low_stock.scalar() or 0,
        }
