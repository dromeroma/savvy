"""Seed data for church denominations and zones."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.church_hierarchy.models import ChurchDenomination, ChurchZone

# System denominations seeded for all tenants.
SYSTEM_DENOMINATIONS = [
    {
        "code": "MMM",
        "name": "Movimiento Misionero Mundial",
        "zones": 132,  # MMM has zones 1..132
    },
]


async def seed_denominations(db: AsyncSession) -> None:
    """Seed system denominations and their zones. Idempotent."""
    for data in SYSTEM_DENOMINATIONS:
        denom = await db.scalar(
            select(ChurchDenomination).where(
                ChurchDenomination.code == data["code"],
                ChurchDenomination.created_by_org_id.is_(None),
            )
        )
        if denom is None:
            denom = ChurchDenomination(
                code=data["code"],
                name=data["name"],
                is_system=True,
                created_by_org_id=None,
            )
            db.add(denom)
            await db.flush()  # generate id

        # Seed zones 1..N
        existing_numbers = set(
            await db.scalars(
                select(ChurchZone.number).where(ChurchZone.denomination_id == denom.id)
            )
        )
        for n in range(1, data["zones"] + 1):
            if n not in existing_numbers:
                db.add(ChurchZone(denomination_id=denom.id, number=n))
    await db.flush()
