"""Business logic for onboarding catalog reads."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.church_hierarchy.models import ChurchDenomination, ChurchZone
from src.modules.organization.models import BusinessTypeCatalog


class OnboardingService:
    """Stateless service serving the signup wizard."""

    @staticmethod
    async def list_business_types(db: AsyncSession) -> list[BusinessTypeCatalog]:
        result = await db.execute(
            select(BusinessTypeCatalog)
            .where(BusinessTypeCatalog.is_active.is_(True))
            .order_by(BusinessTypeCatalog.sort_order, BusinessTypeCatalog.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_denominations(
        db: AsyncSession,
        business_type: str | None = None,
    ) -> list[ChurchDenomination]:
        """Return system denominations.

        Custom denominations are private to the org that created them; they
        are not exposed on this public endpoint.
        """
        if business_type is not None and business_type != "church":
            return []
        result = await db.execute(
            select(ChurchDenomination)
            .where(ChurchDenomination.created_by_org_id.is_(None))
            .order_by(ChurchDenomination.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_zones(
        db: AsyncSession,
        denomination_id: uuid.UUID,
    ) -> list[ChurchZone]:
        result = await db.execute(
            select(ChurchZone)
            .where(ChurchZone.denomination_id == denomination_id)
            .order_by(ChurchZone.number)
        )
        return list(result.scalars().all())


onboarding_service = OnboardingService()
