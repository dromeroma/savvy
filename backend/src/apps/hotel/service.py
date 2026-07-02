"""SavvyHotel business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hotel import availability as avail
from src.apps.hotel.models import (
    HotelFolio,
    HotelFolioCharge,
    HotelFolioPayment,
    HotelReservation,
    HotelRoom,
    HotelRoomType,
)
from src.apps.hotel.schemas import (
    FolioChargeCreate,
    FolioPaymentCreate,
    ReservationCreate,
    RoomCreate,
    RoomTypeCreate,
    RoomTypeUpdate,
    RoomUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Room types

class RoomTypeService:
    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[HotelRoomType]:
        q = select(HotelRoomType).where(HotelRoomType.organization_id == org_id).order_by(HotelRoomType.name)
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: RoomTypeCreate) -> HotelRoomType:
        t = HotelRoomType(organization_id=org_id, **data.model_dump())
        db.add(t)
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def update(db: AsyncSession, org_id: uuid.UUID, tid: uuid.UUID, data: RoomTypeUpdate) -> HotelRoomType:
        t = await db.get(HotelRoomType, tid)
        if not t or t.organization_id != org_id:
            raise NotFoundError("Tipo de habitación no encontrado.")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(t, k, v)
        await db.flush()
        await db.refresh(t)
        return t


# ============================================================ Rooms

class RoomService:
    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[dict]:
        q = (
            select(HotelRoom, HotelRoomType.name)
            .join(HotelRoomType, HotelRoomType.id == HotelRoom.room_type_id)
            .where(HotelRoom.organization_id == org_id)
            .order_by(HotelRoom.number)
        )
        out = []
        for room, type_name in (await db.execute(q)).all():
            d = {c.name: getattr(room, c.name) for c in room.__table__.columns}
            d["room_type_name"] = type_name
            out.append(d)
        return out

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: RoomCreate) -> HotelRoom:
        r = HotelRoom(organization_id=org_id, **data.model_dump())
        db.add(r)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def update(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, data: RoomUpdate) -> HotelRoom:
        r = await db.get(HotelRoom, rid)
        if not r or r.organization_id != org_id:
            raise NotFoundError("Habitación no encontrada.")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(r, k, v)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def set_housekeeping(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, status: str) -> HotelRoom:
        if status not in ("clean", "dirty", "cleaning", "inspected"):
            raise ValidationError("Estado de limpieza inválido.")
        return await RoomService.update(db, org_id, rid, RoomUpdate(housekeeping_status=status))


# ============================================================ Reservations

class ReservationService:
    @staticmethod
    async def _decorate(db: AsyncSession, r: HotelReservation) -> dict:
        d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        t = await db.get(HotelRoomType, r.room_type_id)
        d["room_type_name"] = t.name if t else None
        if r.room_id:
            room = await db.get(HotelRoom, r.room_id)
            d["room_number"] = room.number if room else None
        folio = await db.scalar(select(HotelFolio).where(HotelFolio.reservation_id == r.id))
        d["folio_balance"] = float(folio.balance) if folio else None
        return d

    @staticmethod
    async def list(
        db: AsyncSession, org_id: uuid.UUID, status: str | None = None,
        date_from: date | None = None, date_to: date | None = None,
    ) -> list[dict]:
        q = select(HotelReservation).where(HotelReservation.organization_id == org_id)
        if status:
            q = q.where(HotelReservation.status == status)
        if date_from:
            q = q.where(HotelReservation.check_out_date > date_from)
        if date_to:
            q = q.where(HotelReservation.check_in_date < date_to)
        rows = (await db.execute(q.order_by(HotelReservation.check_in_date))).scalars().all()
        return [await ReservationService._decorate(db, r) for r in rows]

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: ReservationCreate) -> dict:
        if data.check_out_date <= data.check_in_date:
            raise ValidationError("La fecha de salida debe ser posterior a la de entrada.")
        nights = (data.check_out_date - data.check_in_date).days

        rtype = await db.get(HotelRoomType, data.room_type_id)
        if not rtype or rtype.organization_id != org_id:
            raise NotFoundError("Tipo de habitación no encontrado.")

        # Prevención de overbooking a nivel de tipo.
        if not await avail.type_has_availability(
            db, org_id, data.room_type_id, data.check_in_date, data.check_out_date
        ):
            raise ConflictError("No hay disponibilidad para ese tipo en las fechas seleccionadas.")

        # Si se asigna habitación específica, verifica que esté libre.
        if data.room_id:
            free = await avail.available_rooms(
                db, org_id, data.check_in_date, data.check_out_date, data.room_type_id)
            if data.room_id not in {r.id for r in free}:
                raise ConflictError("La habitación seleccionada no está disponible en esas fechas.")

        rate = float(data.rate) if data.rate is not None else float(rtype.base_rate)
        total = rate * nights
        code = f"R-{data.check_in_date:%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"

        r = HotelReservation(
            organization_id=org_id, code=code,
            guest_name=data.guest_name, guest_document=data.guest_document,
            guest_email=data.guest_email, guest_phone=data.guest_phone,
            room_type_id=data.room_type_id, room_id=data.room_id,
            check_in_date=data.check_in_date, check_out_date=data.check_out_date,
            nights=nights, adults=data.adults, children=data.children,
            rate=rate, total=total, status="confirmed", source=data.source, notes=data.notes,
        )
        db.add(r)
        await db.flush()

        # Folio abierto + cargo de alojamiento.
        folio = HotelFolio(organization_id=org_id, reservation_id=r.id, status="open")
        db.add(folio)
        await db.flush()
        db.add(HotelFolioCharge(
            organization_id=org_id, folio_id=folio.id, kind="room",
            description=f"Alojamiento · {nights} noche(s)",
            quantity=nights, unit_price=rate, amount=total, charged_at=_now(),
        ))
        await _recompute_folio(db, folio)
        await db.refresh(r)
        return await ReservationService._decorate(db, r)

    @staticmethod
    async def check_in(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, room_id: uuid.UUID) -> dict:
        r = await db.get(HotelReservation, rid)
        if not r or r.organization_id != org_id:
            raise NotFoundError("Reserva no encontrada.")
        if r.status != "confirmed":
            raise ValidationError(f"Solo se hace check-in a reservas confirmadas (actual: {r.status}).")
        free = await avail.available_rooms(
            db, org_id, r.check_in_date, r.check_out_date, r.room_type_id, exclude_reservation_id=r.id)
        if room_id not in {x.id for x in free}:
            raise ConflictError("Esa habitación no está disponible para el rango de la reserva.")
        room = await db.get(HotelRoom, room_id)
        if not room or room.organization_id != org_id:
            raise NotFoundError("Habitación no encontrada.")
        r.room_id = room_id
        r.status = "checked_in"
        r.checked_in_at = _now()
        room.status = "occupied"
        await db.flush()
        await db.refresh(r)
        return await ReservationService._decorate(db, r)

    @staticmethod
    async def check_out(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID) -> dict:
        r = await db.get(HotelReservation, rid)
        if not r or r.organization_id != org_id:
            raise NotFoundError("Reserva no encontrada.")
        if r.status != "checked_in":
            raise ValidationError("Solo se hace check-out a huéspedes en casa (checked_in).")
        r.status = "checked_out"
        r.checked_out_at = _now()
        if r.room_id:
            room = await db.get(HotelRoom, r.room_id)
            if room:
                room.status = "available"
                room.housekeeping_status = "dirty"
        folio = await db.scalar(select(HotelFolio).where(HotelFolio.reservation_id == r.id))
        if folio:
            folio.status = "closed"
            folio.closed_at = _now()
        await db.flush()
        await db.refresh(r)
        return await ReservationService._decorate(db, r)

    @staticmethod
    async def set_status(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, status: str) -> dict:
        if status not in ("cancelled", "no_show"):
            raise ValidationError("Transición no permitida por este endpoint.")
        r = await db.get(HotelReservation, rid)
        if not r or r.organization_id != org_id:
            raise NotFoundError("Reserva no encontrada.")
        r.status = status
        await db.flush()
        await db.refresh(r)
        return await ReservationService._decorate(db, r)


# ============================================================ Folio

async def _recompute_folio(db: AsyncSession, folio: HotelFolio) -> None:
    charges = (await db.execute(
        select(HotelFolioCharge.amount).where(HotelFolioCharge.folio_id == folio.id))).scalars().all()
    payments = (await db.execute(
        select(HotelFolioPayment.amount).where(HotelFolioPayment.folio_id == folio.id))).scalars().all()
    folio.total_charges = sum((float(c) for c in charges), 0.0)
    folio.total_payments = sum((float(p) for p in payments), 0.0)
    folio.balance = folio.total_charges - folio.total_payments
    await db.flush()


class FolioService:
    @staticmethod
    async def _folio_for_reservation(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID) -> HotelFolio:
        folio = await db.scalar(select(HotelFolio).where(
            HotelFolio.reservation_id == rid, HotelFolio.organization_id == org_id))
        if not folio:
            raise NotFoundError("Folio no encontrado para esa reserva.")
        return folio

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID) -> HotelFolio:
        return await FolioService._folio_for_reservation(db, org_id, rid)

    @staticmethod
    async def add_charge(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, data: FolioChargeCreate) -> HotelFolio:
        folio = await FolioService._folio_for_reservation(db, org_id, rid)
        if folio.status == "closed":
            raise ValidationError("El folio está cerrado.")
        amount = float(data.quantity) * float(data.unit_price)
        db.add(HotelFolioCharge(
            organization_id=org_id, folio_id=folio.id, kind=data.kind,
            description=data.description, quantity=data.quantity, unit_price=data.unit_price,
            amount=amount, reference_id=data.reference_id, charged_at=_now(),
        ))
        await _recompute_folio(db, folio)
        await db.refresh(folio)
        return folio

    @staticmethod
    async def charge_from_pos(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, sale_id: uuid.UUID) -> HotelFolio:
        """Carga una venta de POS (restaurante/minibar) al folio de la habitación."""
        from src.apps.pos.sales.models import PosSale
        sale = await db.get(PosSale, sale_id)
        if not sale or sale.organization_id != org_id:
            raise NotFoundError("Venta de POS no encontrada.")
        if sale.status != "completed":
            raise ValidationError("Solo se cargan ventas completadas.")
        folio = await FolioService._folio_for_reservation(db, org_id, rid)
        if folio.status == "closed":
            raise ValidationError("El folio está cerrado.")
        # Evita duplicar la misma venta.
        dup = await db.scalar(select(HotelFolioCharge.id).where(
            HotelFolioCharge.folio_id == folio.id, HotelFolioCharge.reference_id == sale_id))
        if dup:
            raise ConflictError("Esa venta ya está cargada al folio.")
        db.add(HotelFolioCharge(
            organization_id=org_id, folio_id=folio.id, kind="pos",
            description=f"Consumo POS · {sale.sale_number}",
            quantity=1, unit_price=float(sale.total), amount=float(sale.total),
            reference_id=sale_id, charged_at=_now(),
        ))
        await _recompute_folio(db, folio)
        await db.refresh(folio)
        return folio

    @staticmethod
    async def add_payment(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, data: FolioPaymentCreate) -> HotelFolio:
        folio = await FolioService._folio_for_reservation(db, org_id, rid)
        db.add(HotelFolioPayment(
            organization_id=org_id, folio_id=folio.id, amount=data.amount,
            method=data.method, reference=data.reference, paid_at=_now(),
        ))
        await _recompute_folio(db, folio)
        await db.refresh(folio)
        return folio
