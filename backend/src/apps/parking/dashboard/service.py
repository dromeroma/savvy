"""SavvyParking dashboard KPIs."""

from __future__ import annotations
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.parking.sessions.models import ParkingSession
from src.apps.parking.infrastructure.models import ParkingLocation, ParkingSpot


class ParkingDashboardService:

    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        # Active sessions
        active = await db.execute(select(func.count()).where(ParkingSession.organization_id == org_id, ParkingSession.status == "active"))
        active_sessions = active.scalar() or 0

        # Today revenue
        from datetime import date, datetime, UTC
        today = date.today()
        revenue = await db.execute(select(func.coalesce(func.sum(ParkingSession.total), 0)).where(
            ParkingSession.organization_id == org_id, ParkingSession.status == "completed",
            func.date(ParkingSession.exit_time) == today,
        ))
        today_revenue = float(revenue.scalar() or 0)

        # Total completed today
        completed = await db.execute(select(func.count()).where(
            ParkingSession.organization_id == org_id, ParkingSession.status == "completed",
            func.date(ParkingSession.exit_time) == today,
        ))
        completed_today = completed.scalar() or 0

        # Total capacity & occupancy
        cap = await db.execute(select(
            func.coalesce(func.sum(ParkingLocation.total_capacity), 0),
            func.coalesce(func.sum(ParkingLocation.current_occupancy), 0),
        ).where(ParkingLocation.organization_id == org_id))
        cap_row = cap.one()
        total_capacity = int(cap_row[0])
        current_occupancy = int(cap_row[1])
        occupancy_rate = round((current_occupancy / total_capacity * 100) if total_capacity > 0 else 0, 1)

        # Available spots
        avail = await db.execute(select(func.count()).where(ParkingSpot.organization_id == org_id, ParkingSpot.status == "available"))
        available_spots = avail.scalar() or 0

        return {
            "active_sessions": active_sessions,
            "today_revenue": today_revenue,
            "completed_today": completed_today,
            "total_capacity": total_capacity,
            "current_occupancy": current_occupancy,
            "occupancy_rate": occupancy_rate,
            "available_spots": available_spots,
        }
