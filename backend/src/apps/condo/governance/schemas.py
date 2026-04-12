"""Pydantic schemas for condo governance."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class ProposalSchema(BaseModel):
    title: str; description: str | None = None

class AssemblyCreate(BaseModel):
    property_id: uuid.UUID; title: str = Field(..., max_length=200); description: str | None = None
    assembly_type: Literal["ordinary", "extraordinary"] = "ordinary"
    scheduled_at: datetime; quorum_required: float = Field(51.0, ge=0, le=100)
    proposals: list[ProposalSchema] = Field(default_factory=list)

class AssemblyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; property_id: uuid.UUID; title: str; description: str | None = None
    assembly_type: str; scheduled_at: datetime; quorum_required: float; quorum_present: float
    proposals: list[dict[str, Any]]; minutes: str | None = None; status: str; created_at: datetime

class VoteCreate(BaseModel):
    assembly_id: uuid.UUID; unit_id: uuid.UUID; proposal_index: int = 0
    vote: Literal["yes", "no", "abstain"]

class VoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; assembly_id: uuid.UUID; unit_id: uuid.UUID; proposal_index: int
    vote: str; coefficient_weight: float
