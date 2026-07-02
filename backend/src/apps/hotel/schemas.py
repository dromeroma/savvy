"""SavvyHotel Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ----------------------------- Room types -----------------------------

class RoomTypeCreate(BaseModel):
    code: str
    name: str
    capacity: int = 2
    base_rate: float = 0
    description: str | None = None
    amenities: list[str] = Field(default_factory=list)


class RoomTypeUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    base_rate: float | None = None
    description: str | None = None
    amenities: list[str] | None = None
    status: str | None = None


class RoomTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    capacity: int
    base_rate: float
    description: str | None
    amenities: list
    status: str


# ------------------------------- Rooms -------------------------------

class RoomCreate(BaseModel):
    room_type_id: uuid.UUID
    number: str
    floor: str | None = None
    notes: str | None = None


class RoomUpdate(BaseModel):
    room_type_id: uuid.UUID | None = None
    number: str | None = None
    floor: str | None = None
    status: str | None = None
    housekeeping_status: str | None = None
    notes: str | None = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    room_type_id: uuid.UUID
    number: str
    floor: str | None
    status: str
    housekeeping_status: str
    notes: str | None
    room_type_name: str | None = None


# --------------------------- Availability ---------------------------

class AvailabilityRow(BaseModel):
    room_type_id: uuid.UUID
    room_type_name: str
    base_rate: float
    total_rooms: int
    available: int


class AvailabilityResponse(BaseModel):
    check_in: date
    check_out: date
    nights: int
    rows: list[AvailabilityRow]


# --------------------------- Reservations ---------------------------

class ReservationCreate(BaseModel):
    guest_name: str
    guest_document: str | None = None
    guest_email: str | None = None
    guest_phone: str | None = None
    room_type_id: uuid.UUID
    room_id: uuid.UUID | None = None
    check_in_date: date
    check_out_date: date
    adults: int = 1
    children: int = 0
    rate: float | None = None  # si no viene, usa base_rate del tipo
    source: str = "direct"
    notes: str | None = None


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    guest_name: str
    guest_document: str | None
    guest_email: str | None
    guest_phone: str | None
    room_type_id: uuid.UUID
    room_id: uuid.UUID | None
    check_in_date: date
    check_out_date: date
    nights: int
    adults: int
    children: int
    rate: float
    total: float
    status: str
    source: str
    notes: str | None
    room_type_name: str | None = None
    room_number: str | None = None
    folio_balance: float | None = None


class CheckInRequest(BaseModel):
    room_id: uuid.UUID


# ------------------------------ Folio ------------------------------

class FolioChargeCreate(BaseModel):
    kind: str = "service"
    description: str
    quantity: float = 1
    unit_price: float
    reference_id: uuid.UUID | None = None


class ChargeFromPosRequest(BaseModel):
    sale_id: uuid.UUID


class FolioPaymentCreate(BaseModel):
    amount: float
    method: str = "cash"
    reference: str | None = None


class FolioChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    kind: str
    description: str
    quantity: float
    unit_price: float
    amount: float
    charged_at: datetime


class FolioPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    amount: float
    method: str
    reference: str | None
    paid_at: datetime


class FolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reservation_id: uuid.UUID
    status: str
    total_charges: float
    total_payments: float
    balance: float
    closed_at: datetime | None
    charges: list[FolioChargeResponse] = []
    payments: list[FolioPaymentResponse] = []


# ---------------------------- Housekeeping ----------------------------

class HousekeepingUpdate(BaseModel):
    housekeeping_status: str  # clean, dirty, cleaning, inspected


# ----------------------------- Dashboard -----------------------------

class HotelDashboard(BaseModel):
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    arrivals_today: int
    departures_today: int
    in_house: int
    adr: float          # tarifa promedio diaria
    revpar: float       # ingreso por habitación disponible
    revenue_today: float
    dirty_rooms: int
