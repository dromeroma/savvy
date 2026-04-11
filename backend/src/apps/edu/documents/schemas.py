"""Pydantic v2 schemas for SavvyEdu documents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DOC_TYPE = Literal["certificate", "transcript", "report_card", "paz_y_salvo"]


class DocumentTemplateCreate(BaseModel):
    type: DOC_TYPE
    name: str = Field(..., min_length=1, max_length=200)
    template_html: str | None = None
    variables: list[str] | None = None


class DocumentTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    name: str
    template_html: str | None = None
    variables: Any = None
    created_at: datetime


class IssuedDocumentCreate(BaseModel):
    student_id: uuid.UUID
    template_id: uuid.UUID
    data: dict[str, Any] = Field(default_factory=dict)


class IssuedDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    student_id: uuid.UUID
    template_id: uuid.UUID
    data: dict[str, Any]
    issued_at: datetime
    issued_by: uuid.UUID | None = None
