"""Pydantic v2 schemas for SavvyFamily."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Family Unit
# ---------------------------------------------------------------------------

FAMILY_TYPE = Literal["nuclear", "extended", "single_parent", "blended", "other"]


class FamilyUnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: FAMILY_TYPE = "nuclear"
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    notes: str | None = None


class FamilyUnitUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    type: FAMILY_TYPE | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    notes: str | None = None
    status: Literal["active", "inactive"] | None = None


class FamilyUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    type: str
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Family Member
# ---------------------------------------------------------------------------

MEMBER_ROLE = Literal["head", "spouse", "child", "grandchild", "grandparent", "uncle_aunt", "cousin", "in_law", "other", "member"]


class FamilyMemberCreate(BaseModel):
    person_id: uuid.UUID
    role: MEMBER_ROLE = "member"
    is_deceased: bool = False
    death_date: date | None = None
    generation: int = 0


class FamilyMemberUpdate(BaseModel):
    role: MEMBER_ROLE | None = None
    is_deceased: bool | None = None
    death_date: date | None = None
    generation: int | None = None
    position_x: int | None = None
    position_y: int | None = None


class FamilyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    family_unit_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    is_deceased: bool
    death_date: date | None = None
    generation: int
    position_x: int | None = None
    position_y: int | None = None
    created_at: datetime

    # Populated by service
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    photo_url: str | None = None
    marital_status: str | None = None


# ---------------------------------------------------------------------------
# Relationship Metadata
# ---------------------------------------------------------------------------

REL_TYPE = Literal["married", "divorced", "separated", "engaged", "cohabiting", "widowed"]


class RelationshipMetaCreate(BaseModel):
    person_id: uuid.UUID
    related_to_id: uuid.UUID
    relationship_type: REL_TYPE
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class RelationshipMetaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    family_unit_id: uuid.UUID
    person_id: uuid.UUID
    related_to_id: uuid.UUID
    relationship_type: str
    start_date: date | None = None
    end_date: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

ANNOTATION_CATEGORY = Literal[
    "substance_abuse", "mental_health", "physical_illness", "violence",
    "sexual_abuse", "emotional_abuse", "conflict", "cutoff", "enmeshment",
    "estrangement", "disability", "incarceration", "adoption",
    "miscarriage", "abortion", "stillbirth", "spiritual", "financial", "other",
]

SEVERITY = Literal["mild", "moderate", "severe"]


class AnnotationCreate(BaseModel):
    person_id: uuid.UUID | None = None
    category: ANNOTATION_CATEGORY
    severity: SEVERITY = "moderate"
    description: str | None = None
    diagnosed_date: date | None = None
    source_app: str | None = Field(None, max_length=20)


class AnnotationUpdate(BaseModel):
    severity: SEVERITY | None = None
    description: str | None = None
    is_active: bool | None = None
    resolved_date: date | None = None


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    family_unit_id: uuid.UUID
    person_id: uuid.UUID | None = None
    category: str
    severity: str
    description: str | None = None
    is_active: bool
    diagnosed_date: date | None = None
    resolved_date: date | None = None
    source_app: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Genogram Data (composite response for rendering)
# ---------------------------------------------------------------------------


class GenogramNode(BaseModel):
    """A node in the genogram (person)."""
    id: uuid.UUID
    person_id: uuid.UUID
    first_name: str
    last_name: str
    gender: str | None = None
    date_of_birth: date | None = None
    is_deceased: bool = False
    death_date: date | None = None
    role: str
    generation: int
    position_x: int | None = None
    position_y: int | None = None
    annotations: list[AnnotationResponse] = Field(default_factory=list)


class GenogramEdge(BaseModel):
    """A relationship edge between two nodes."""
    source_person_id: uuid.UUID
    target_person_id: uuid.UUID
    relationship_type: str  # married, divorced, parent_child, sibling
    status: str = "active"


class GenogramData(BaseModel):
    """Complete genogram data for rendering."""
    family_unit: FamilyUnitResponse
    nodes: list[GenogramNode]
    edges: list[GenogramEdge]
