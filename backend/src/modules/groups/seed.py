"""Default seed data for group types."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.groups.models import GroupType

CHURCH_GROUP_TYPES = [
    {
        "code": "ministry",
        "name": "Ministerio",
        "app_code": "church",
        "allow_hierarchy": True,
        "requires_attendance": True,
        "requires_activities": True,
    },
    {
        "code": "cell",
        "name": "Célula",
        "app_code": "church",
        "requires_attendance": True,
        "max_members": 15,
    },
    {
        "code": "committee",
        "name": "Comité",
        "app_code": "church",
        "requires_activities": True,
    },
    {
        "code": "service_team",
        "name": "Equipo de Servicio",
        "app_code": "church",
        "requires_attendance": True,
    },
]


async def seed_church_group_types(db: AsyncSession, org_id: uuid.UUID) -> list[GroupType]:
    """Insert default church group types for an organization if they don't exist.

    Returns the list of created (or already existing) GroupType instances.
    """
    results: list[GroupType] = []

    for entry in CHURCH_GROUP_TYPES:
        existing = await db.execute(
            select(GroupType).where(
                GroupType.organization_id == org_id,
                GroupType.code == entry["code"],
            )
        )
        group_type = existing.scalar_one_or_none()

        if group_type is None:
            group_type = GroupType(
                organization_id=org_id,
                code=entry["code"],
                name=entry["name"],
                app_code=entry.get("app_code"),
                allow_hierarchy=entry.get("allow_hierarchy", False),
                requires_classes=entry.get("requires_classes", False),
                requires_attendance=entry.get("requires_attendance", False),
                requires_activities=entry.get("requires_activities", False),
                max_members=entry.get("max_members"),
            )
            db.add(group_type)
            await db.flush()
            await db.refresh(group_type)

        results.append(group_type)

    return results
