"""SavvyHotel models — tipos, habitaciones, reservas, folios y cargos."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HotelRoomType(BaseMixin, OrgMixin, Base):
    """Tipo de habitación (sencilla, doble, suite)."""
    __tablename__ = "hotel_room_types"

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    base_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class HotelRoom(BaseMixin, OrgMixin, Base):
    """Habitación física."""
    __tablename__ = "hotel_rooms"

    room_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotel_room_types.id", ondelete="RESTRICT"), nullable=False)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # available, occupied, maintenance, blocked
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    # clean, dirty, cleaning, inspected
    housekeeping_status: Mapped[str] = mapped_column(String(20), nullable=False, default="clean")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class HotelReservation(BaseMixin, OrgMixin, Base):
    """Reserva de estadía."""
    __tablename__ = "hotel_reservations"

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    guest_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_document: Mapped[str | None] = mapped_column(String(40), nullable=True)
    guest_email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    room_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotel_room_types.id", ondelete="RESTRICT"), nullable=False)
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hotel_rooms.id", ondelete="SET NULL"), nullable=True)

    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    adults: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # confirmed, checked_in, checked_out, cancelled, no_show
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    # direct, walk_in, phone, ota
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="direct")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HotelFolio(BaseMixin, OrgMixin, Base):
    """Cuenta de la estadía: acumula cargos y pagos."""
    __tablename__ = "hotel_folios"

    reservation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotel_reservations.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")  # open, closed
    total_charges: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_payments: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    charges: Mapped[list["HotelFolioCharge"]] = relationship(
        back_populates="folio", cascade="all, delete-orphan", lazy="selectin")
    payments: Mapped[list["HotelFolioPayment"]] = relationship(
        back_populates="folio", cascade="all, delete-orphan", lazy="selectin")


class HotelFolioCharge(BaseMixin, OrgMixin, Base):
    """Un cargo en el folio (noche, consumo POS, servicio)."""
    __tablename__ = "hotel_folio_charges"

    folio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotel_folios.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="service")  # room, pos, service, other
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)  # p.ej. pos_sale.id
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    charged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    folio: Mapped[HotelFolio] = relationship(back_populates="charges")


class HotelFolioPayment(BaseMixin, OrgMixin, Base):
    """Pago aplicado al folio."""
    __tablename__ = "hotel_folio_payments"

    folio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hotel_folios.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")  # cash, card, transfer
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    folio: Mapped[HotelFolio] = relationship(back_populates="payments")
