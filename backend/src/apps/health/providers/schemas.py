"""Pydantic schemas for health providers."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ProviderCreate(BaseModel):
    first_name: str = Field(..., max_length=100); last_name: str = Field(..., max_length=100)
    email: EmailStr | None = None; phone: str | None = Field(None, max_length=50)
    document_number: str | None = Field(None, max_length=50)
    provider_code: str | None = Field(None, max_length=30)
    specialty: str = Field(..., max_length=100)
    license_number: str | None = Field(None, max_length=50)
    consultation_duration: int = Field(30, ge=5)

class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; person_id: uuid.UUID
    first_name: str; last_name: str; email: str | None = None; phone: str | None = None
    provider_code: str | None = None; specialty: str; license_number: str | None = None
    consultation_duration: int; schedule: dict[str, Any]; status: str; created_at: datetime
