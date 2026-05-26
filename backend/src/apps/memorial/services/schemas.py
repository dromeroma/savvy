"""Pydantic schemas para servicios funerarios."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ServiceStatus = Literal[
    "iniciado", "en_proceso", "pendiente", "finalizado", "cancelado",
]
ServiceType = Literal[
    "velacion", "cremacion", "entierro",
    "velacion_cremacion", "velacion_entierro",
    "velacion_cremacion_entierro",
]


# ---------------------------------------------------------------- Family


class FamilyMemberBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    relationship: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=255)
    is_primary: bool = False
    notes: str | None = None


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    relationship: str | None = None
    phone: str | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    is_primary: bool | None = None
    notes: str | None = None


class FamilyMemberResponse(FamilyMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Service


class ServiceBase(BaseModel):
    deceased_first_name: str = Field(..., min_length=1, max_length=100)
    deceased_last_name: str | None = Field(None, max_length=100)
    deceased_document_type: str | None = Field(None, max_length=10)
    deceased_document_number: str | None = Field(None, max_length=50)
    deceased_birth_date: date | None = None
    deceased_death_date: date
    deceased_death_time: time | None = None
    deceased_death_cause: str | None = Field(None, max_length=255)
    deceased_death_place: str | None = Field(None, max_length=255)

    service_type: ServiceType
    status: ServiceStatus = "iniciado"

    velation_start_at: datetime | None = None
    velation_end_at: datetime | None = None
    velation_location: str | None = Field(None, max_length=255)

    cremation_at: datetime | None = None
    cremation_location: str | None = Field(None, max_length=255)

    burial_at: datetime | None = None
    burial_cemetery: str | None = Field(None, max_length=255)
    burial_section: str | None = Field(None, max_length=100)

    mass_at: datetime | None = None
    mass_church: str | None = Field(None, max_length=255)

    estimated_total: Decimal = Field(default=Decimal("0"), ge=0)
    final_total: Decimal = Field(default=Decimal("0"), ge=0)

    notes: str | None = None


class ServiceCreate(ServiceBase):
    """Crear un servicio + (opcional) sembrar familiares en el mismo
    request para reducir el round-trip del UI."""

    family_members: list[FamilyMemberCreate] = []


class ServiceUpdate(BaseModel):
    deceased_first_name: str | None = Field(None, min_length=1, max_length=100)
    deceased_last_name: str | None = None
    deceased_document_type: str | None = None
    deceased_document_number: str | None = None
    deceased_birth_date: date | None = None
    deceased_death_date: date | None = None
    deceased_death_time: time | None = None
    deceased_death_cause: str | None = None
    deceased_death_place: str | None = None

    service_type: ServiceType | None = None

    velation_start_at: datetime | None = None
    velation_end_at: datetime | None = None
    velation_location: str | None = None

    cremation_at: datetime | None = None
    cremation_location: str | None = None

    burial_at: datetime | None = None
    burial_cemetery: str | None = None
    burial_section: str | None = None

    mass_at: datetime | None = None
    mass_church: str | None = None

    estimated_total: Decimal | None = Field(None, ge=0)
    final_total: Decimal | None = Field(None, ge=0)

    notes: str | None = None


class ServiceListItem(BaseModel):
    """Resumen compacto para la grilla."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    consecutive: int
    deceased_name: str
    deceased_death_date: date
    service_type: str
    status: str
    estimated_total: Decimal
    final_total: Decimal
    primary_family_name: str | None
    primary_family_phone: str | None
    family_count: int
    created_at: datetime


class ServiceResponse(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    closed_at: datetime | None = None
    closed_by: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    exequial_contract_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    family_members: list[FamilyMemberResponse] = []


class ServiceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    event_type: str
    body: str | None
    event_data: dict | None
    actor_user_id: uuid.UUID | None
    created_at: datetime


class StatusTransitionRequest(BaseModel):
    """Cambio de estado del servicio. El motor valida que la transición
    sea legal (ej. no se puede pasar de finalizado a iniciado)."""

    new_status: ServiceStatus
    note: str | None = None


class AddNoteRequest(BaseModel):
    body: str = Field(..., min_length=1)


class DashboardKpis(BaseModel):
    """Métricas que pinta el dashboard de Memorial — fase 1 son las
    operativas; financieras y de cartera vienen en fase 3."""

    services_total: int
    services_active: int          # iniciado | en_proceso | pendiente
    services_closed: int
    services_today: int           # finalizados o creados hoy
    services_by_status: dict[str, int]
