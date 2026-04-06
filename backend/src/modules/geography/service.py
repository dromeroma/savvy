"""Business logic for geography reference data lookups."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.geography.models import GeoCity, GeoCountry, GeoState


class GeoService:
    """Stateless service layer for geography data queries."""

    # ------------------------------------------------------------------
    # Countries
    # ------------------------------------------------------------------

    @staticmethod
    async def list_countries(db: AsyncSession) -> list[GeoCountry]:
        """Return all active countries ordered by name."""
        result = await db.execute(
            select(GeoCountry)
            .where(GeoCountry.is_active.is_(True))
            .order_by(GeoCountry.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search_countries(db: AsyncSession, query: str) -> list[GeoCountry]:
        """Search active countries by name or code (ILIKE), limit 20."""
        pattern = f"%{query}%"
        result = await db.execute(
            select(GeoCountry)
            .where(
                GeoCountry.is_active.is_(True),
                (GeoCountry.name.ilike(pattern)) | (GeoCountry.code.ilike(pattern)),
            )
            .order_by(GeoCountry.name)
            .limit(20)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # States
    # ------------------------------------------------------------------

    @staticmethod
    async def list_states(db: AsyncSession, country_id: int) -> list[GeoState]:
        """Return all states for a given country ordered by name."""
        result = await db.execute(
            select(GeoState)
            .where(GeoState.country_id == country_id)
            .order_by(GeoState.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search_states(
        db: AsyncSession, country_id: int, query: str
    ) -> list[GeoState]:
        """Search states by name (ILIKE) within a country, limit 20."""
        pattern = f"%{query}%"
        result = await db.execute(
            select(GeoState)
            .where(
                GeoState.country_id == country_id,
                GeoState.name.ilike(pattern),
            )
            .order_by(GeoState.name)
            .limit(20)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Cities
    # ------------------------------------------------------------------

    @staticmethod
    async def list_cities(db: AsyncSession, state_id: int) -> list[GeoCity]:
        """Return all cities for a given state ordered by name."""
        result = await db.execute(
            select(GeoCity)
            .where(GeoCity.state_id == state_id)
            .order_by(GeoCity.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search_cities(
        db: AsyncSession, state_id: int, query: str
    ) -> list[GeoCity]:
        """Search cities by name (ILIKE) within a state, limit 20."""
        pattern = f"%{query}%"
        result = await db.execute(
            select(GeoCity)
            .where(
                GeoCity.state_id == state_id,
                GeoCity.name.ilike(pattern),
            )
            .order_by(GeoCity.name)
            .limit(20)
        )
        return list(result.scalars().all())
