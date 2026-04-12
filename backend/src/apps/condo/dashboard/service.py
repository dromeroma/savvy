"""SavvyCondo dashboard KPIs."""

from __future__ import annotations
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.condo.properties.models import CondoProperty, CondoUnit
from src.apps.condo.fees.models import CondoFee
from src.apps.condo.maintenance.models import CondoMaintenance
from src.apps.condo.residents.models import CondoResident


class CondoDashboardService:
    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        props = await db.execute(select(func.count()).where(CondoProperty.organization_id == org_id))
        units = await db.execute(select(func.count()).where(CondoUnit.organization_id == org_id))
        residents = await db.execute(select(func.count()).where(CondoResident.organization_id == org_id, CondoResident.status == "active"))

        pending_fees = await db.execute(select(
            func.count().label("count"),
            func.coalesce(func.sum(CondoFee.total - CondoFee.paid_amount), 0).label("amount"),
        ).where(CondoFee.organization_id == org_id, CondoFee.status.in_(["pending", "partial", "overdue"])))
        pf = pending_fees.one()

        open_maintenance = await db.execute(select(func.count()).where(CondoMaintenance.organization_id == org_id, CondoMaintenance.status.in_(["open", "in_progress"])))

        return {
            "total_properties": props.scalar() or 0,
            "total_units": units.scalar() or 0,
            "active_residents": residents.scalar() or 0,
            "pending_fees_count": pf.count,
            "pending_fees_amount": float(pf.amount),
            "open_maintenance": open_maintenance.scalar() or 0,
        }
