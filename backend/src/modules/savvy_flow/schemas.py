"""SavvyFlow Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StepIn(BaseModel):
    kind: str  # condition | action
    type: str
    config: dict[str, Any] = {}
    sort_order: int = 0


class StepOut(StepIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any] = {}
    is_active: bool = True
    steps: list[StepIn] = []


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    is_active: bool | None = None
    steps: list[StepIn] | None = None


class WorkflowListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    trigger_type: str
    is_active: bool
    run_count: int
    last_run_at: datetime | None
    last_status: str | None
    created_at: datetime


class WorkflowDetail(WorkflowListItem):
    trigger_config: dict[str, Any]
    steps: list[StepOut]


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    trigger_source: str | None
    items_matched: int
    log: list[dict[str, Any]]
    error: str | None
    started_at: datetime
    finished_at: datetime | None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    level: str
    title: str
    body: str | None
    link: str | None
    read_at: datetime | None
    created_at: datetime


class InstallTemplate(BaseModel):
    template_key: str


class CatalogResponse(BaseModel):
    triggers: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    conditions: list[dict[str, Any]]
    templates: list[dict[str, Any]]


class EvaluateResult(BaseModel):
    evaluated: int
    executed: int
    skipped: int
