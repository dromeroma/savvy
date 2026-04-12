"""Pydantic schemas for health clinical records."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class ClinicalRecordCreate(BaseModel):
    patient_id: uuid.UUID; provider_id: uuid.UUID | None = None; appointment_id: uuid.UUID | None = None
    record_date: date; chief_complaint: str | None = None; present_illness: str | None = None
    physical_exam: str | None = None; assessment: str | None = None; plan: str | None = None
    clinical_data: dict[str, Any] = Field(default_factory=dict)

class ClinicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; patient_id: uuid.UUID; provider_id: uuid.UUID | None = None
    record_date: date; chief_complaint: str | None = None; present_illness: str | None = None
    physical_exam: str | None = None; assessment: str | None = None; plan: str | None = None
    clinical_data: dict[str, Any]; status: str; created_at: datetime

class VitalsCreate(BaseModel):
    record_id: uuid.UUID; patient_id: uuid.UUID
    systolic_bp: int | None = None; diastolic_bp: int | None = None; heart_rate: int | None = None
    temperature: float | None = None; respiratory_rate: int | None = None; oxygen_saturation: int | None = None
    weight_kg: float | None = None; height_cm: float | None = None

class VitalsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; record_id: uuid.UUID; systolic_bp: int | None = None; diastolic_bp: int | None = None
    heart_rate: int | None = None; temperature: float | None = None; weight_kg: float | None = None
    height_cm: float | None = None; created_at: datetime

class DiagnosisCreate(BaseModel):
    record_id: uuid.UUID; patient_id: uuid.UUID; code: str | None = Field(None, max_length=20)
    name: str = Field(..., max_length=300); diagnosis_type: Literal["primary", "secondary", "differential"] = "primary"

class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; record_id: uuid.UUID; code: str | None = None; name: str; diagnosis_type: str

class PrescriptionCreate(BaseModel):
    record_id: uuid.UUID; patient_id: uuid.UUID; medication: str = Field(..., max_length=200)
    dosage: str = Field(..., max_length=100); frequency: str = Field(..., max_length=100)
    duration: str | None = Field(None, max_length=50); instructions: str | None = None

class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; record_id: uuid.UUID; medication: str; dosage: str; frequency: str
    duration: str | None = None; instructions: str | None = None; status: str

class LabOrderCreate(BaseModel):
    patient_id: uuid.UUID; record_id: uuid.UUID | None = None; provider_id: uuid.UUID | None = None
    test_name: str = Field(..., max_length=200); test_code: str | None = Field(None, max_length=20)
    urgency: Literal["routine", "urgent", "stat"] = "routine"

class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; patient_id: uuid.UUID; test_name: str; test_code: str | None = None
    urgency: str; status: str; results: dict | None = None; created_at: datetime
