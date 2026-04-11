"""Pydantic v2 schemas for SavvyEdu teachers."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


TEACHER_STATUS = Literal["active", "inactive", "on_leave"]
CONTRACT_TYPE = Literal["full_time", "part_time", "adjunct"]


class TeacherCreate(BaseModel):
    # Person fields
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=10)
    state: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    address: str | None = None

    # Teacher fields
    employee_code: str = Field(..., min_length=1, max_length=30)
    department_scope_id: uuid.UUID | None = None
    specialization: str | None = Field(None, max_length=200)
    hire_date: date | None = None
    contract_type: CONTRACT_TYPE | None = None
    bio: str | None = None


class TeacherUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=10)
    state: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    address: str | None = None

    department_scope_id: uuid.UUID | None = None
    specialization: str | None = Field(None, max_length=200)
    hire_date: date | None = None
    contract_type: CONTRACT_TYPE | None = None
    bio: str | None = None
    status: TEACHER_STATUS | None = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID

    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    address: str | None = None
    photo_url: str | None = None

    employee_code: str
    department_scope_id: uuid.UUID | None = None
    specialization: str | None = None
    hire_date: date | None = None
    contract_type: str | None = None
    bio: str | None = None
    status: str

    created_at: datetime
    updated_at: datetime


class TeacherListParams(BaseModel):
    search: str | None = None
    status: TEACHER_STATUS | None = None
    department_scope_id: uuid.UUID | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
