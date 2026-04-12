"""Business logic for health appointments."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.health.appointments.models import HealthAppointment
from src.apps.health.appointments.schemas import AppointmentCreate, AppointmentUpdate
from src.apps.health.services.models import HealthService


class AppointmentService:
    @staticmethod
    async def list_appointments(db: AsyncSession, org_id: uuid.UUID, provider_id: uuid.UUID | None = None, patient_id: uuid.UUID | None = None, status_filter: str | None = None) -> list[HealthAppointment]:
        q = select(HealthAppointment).where(HealthAppointment.organization_id == org_id)
        if provider_id: q = q.where(HealthAppointment.provider_id == provider_id)
        if patient_id: q = q.where(HealthAppointment.patient_id == patient_id)
        if status_filter: q = q.where(HealthAppointment.status == status_filter)
        return list((await db.execute(q.order_by(HealthAppointment.appointment_date.desc(), HealthAppointment.start_time))).scalars().all())

    @staticmethod
    async def create_appointment(db: AsyncSession, org_id: uuid.UUID, data: AppointmentCreate) -> HealthAppointment:
        amount = 0.0
        if data.service_id:
            svc = await db.execute(select(HealthService).where(HealthService.id == data.service_id))
            s = svc.scalar_one_or_none()
            if s: amount = float(s.price)
        apt = HealthAppointment(organization_id=org_id, amount=amount, **data.model_dump())
        db.add(apt); await db.flush(); await db.refresh(apt); return apt

    @staticmethod
    async def update_appointment(db: AsyncSession, org_id: uuid.UUID, apt_id: uuid.UUID, data: AppointmentUpdate) -> HealthAppointment:
        result = await db.execute(select(HealthAppointment).where(HealthAppointment.id == apt_id, HealthAppointment.organization_id == org_id))
        apt = result.scalar_one_or_none()
        if apt is None: raise NotFoundError("Appointment not found.")
        for f, v in data.model_dump(exclude_unset=True).items(): setattr(apt, f, v)
        await db.flush(); await db.refresh(apt); return apt
