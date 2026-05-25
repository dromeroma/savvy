"""Audit schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_name: str | None = None
    action: str
    resource_type: str | None
    resource_id: uuid.UUID | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
