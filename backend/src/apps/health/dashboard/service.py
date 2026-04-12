"""SavvyHealth dashboard KPIs."""

from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.health.patients.models import HealthPatient
from src.apps.health.providers.models import HealthProvider
from src.apps.health.appointments.models import HealthAppointment


class HealthDashboardService:
    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        patients = await db.execute(select(func.count()).where(HealthPatient.organization_id == org_id))
        providers = await db.execute(select(func.count()).where(HealthProvider.organization_id == org_id))
        today = date.today()
        today_apts = await db.execute(select(func.count()).where(HealthAppointment.organization_id == org_id, HealthAppointment.appointment_date == today))
        pending_apts = await db.execute(select(func.count()).where(HealthAppointment.organization_id == org_id, HealthAppointment.status.in_(["scheduled", "confirmed"])))
        completed = await db.execute(select(func.count()).where(HealthAppointment.organization_id == org_id, HealthAppointment.status == "completed"))
        revenue = await db.execute(select(func.coalesce(func.sum(HealthAppointment.amount), 0)).where(HealthAppointment.organization_id == org_id, HealthAppointment.payment_status == "paid"))

        return {
            "total_patients": patients.scalar() or 0,
            "total_providers": providers.scalar() or 0,
            "today_appointments": today_apts.scalar() or 0,
            "pending_appointments": pending_apts.scalar() or 0,
            "completed_appointments": completed.scalar() or 0,
            "total_revenue": float(revenue.scalar() or 0),
        }
