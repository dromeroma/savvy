"""Pydantic schemas for health patients."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class PatientCreate(BaseModel):
    first_name: str = Field(..., max_length=100); last_name: str = Field(..., max_length=100)
    email: EmailStr | None = None; phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None; gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20); document_number: str | None = Field(None, max_length=50)
    address: str | None = None; city: str | None = Field(None, max_length=100)
    patient_code: str | None = Field(None, max_length=30)
    blood_type: str | None = Field(None, max_length=5)
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)

class PatientUpdate(BaseModel):
    blood_type: str | None = Field(None, max_length=5)
    allergies: list[str] | None = None; chronic_conditions: list[str] | None = None
    current_medications: list[str] | None = None; notes: str | None = None
    status: Literal["active", "inactive"] | None = None

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; person_id: uuid.UUID
    first_name: str; last_name: str; email: str | None = None; phone: str | None = None
    date_of_birth: date | None = None; gender: str | None = None
    document_type: str | None = None; document_number: str | None = None
    patient_code: str | None = None; blood_type: str | None = None
    allergies: list[str]; chronic_conditions: list[str]; current_medications: list[str]
    notes: str | None = None; status: str; created_at: datetime

class InsuranceCreate(BaseModel):
    patient_id: uuid.UUID; provider_name: str = Field(..., max_length=200)
    policy_number: str | None = Field(None, max_length=50)
    plan_type: str | None = Field(None, max_length=50)

class InsuranceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; patient_id: uuid.UUID; provider_name: str
    policy_number: str | None = None; plan_type: str | None = None; is_active: bool
