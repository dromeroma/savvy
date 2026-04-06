"""FastAPI router for public geography reference data endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.modules.geography.schemas import CityResponse, CountryResponse, StateResponse
from src.modules.geography.service import GeoService

router = APIRouter(prefix="/geography", tags=["Geography"])


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------


@router.get("/countries", response_model=list[CountryResponse])
async def list_countries(
    q: str | None = Query(None, description="Search by name or code"),
    db: AsyncSession = Depends(get_db),
) -> list[CountryResponse]:
    """List all active countries, or search by name/code if ?q= is provided."""
    if q:
        return await GeoService.search_countries(db, q)
    return await GeoService.list_countries(db)


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------


@router.get("/countries/{country_id}/states", response_model=list[StateResponse])
async def list_states(
    country_id: int,
    q: str | None = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
) -> list[StateResponse]:
    """List all states for a country, or search by name if ?q= is provided."""
    if q:
        return await GeoService.search_states(db, country_id, q)
    return await GeoService.list_states(db, country_id)


# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------


@router.get("/states/{state_id}/cities", response_model=list[CityResponse])
async def list_cities(
    state_id: int,
    q: str | None = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
) -> list[CityResponse]:
    """List all cities for a state, or search by name if ?q= is provided."""
    if q:
        return await GeoService.search_cities(db, state_id, q)
    return await GeoService.list_cities(db, state_id)
