"""Pydantic schemas for CSV imports."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel


class ImportRowError(BaseModel):
    field: str
    message: str


class ImportRowPreview(BaseModel):
    """One row of the parsed CSV after validation."""

    row_number: int
    action: Literal["create", "update", "error"]
    data: dict[str, Any]
    errors: list[ImportRowError] = []
    existing_id: uuid.UUID | None = None


class ImportPreviewResponse(BaseModel):
    rows: list[ImportRowPreview]
    total_rows: int
    total_valid: int
    total_errors: int
    total_create: int
    total_update: int


class ImportCommitRow(BaseModel):
    """A row the client wants committed.

    The frontend echoes back the validated rows from /preview so we can
    apply them in a single transaction without re-uploading the file.
    """

    row_number: int
    action: Literal["create", "update"]
    data: dict[str, Any]
    existing_id: uuid.UUID | None = None


class SubscribersCommitRequest(BaseModel):
    rows: list[ImportCommitRow]


class MetersCommitRequest(BaseModel):
    rows: list[ImportCommitRow]


class ImportCommitResponse(BaseModel):
    created: int
    updated: int
    failed: int
    errors: list[ImportRowError] = []
