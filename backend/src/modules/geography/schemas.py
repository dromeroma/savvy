"""Pydantic response schemas for geography endpoints."""

from pydantic import BaseModel, ConfigDict


class CountryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    phone_code: str | None = None
    currency: str | None = None


class StateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int
    code: str
    name: str


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state_id: int
    code: str | None = None
    name: str
