"""SavvyCRM dashboard KPIs."""

from __future__ import annotations
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.crm.deals.models import CrmDeal
from src.apps.crm.contacts.models import CrmContact
from src.apps.crm.leads.models import CrmLead


class CrmDashboardService:

    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        # Deals
        deals = await db.execute(select(
            func.count().label("total_deals"),
            func.count().filter(CrmDeal.status == "open").label("open_deals"),
            func.count().filter(CrmDeal.status == "won").label("won_deals"),
            func.count().filter(CrmDeal.status == "lost").label("lost_deals"),
            func.coalesce(func.sum(CrmDeal.value).filter(CrmDeal.status == "open"), 0).label("pipeline_value"),
            func.coalesce(func.sum(CrmDeal.value).filter(CrmDeal.status == "won"), 0).label("won_value"),
        ).where(CrmDeal.organization_id == org_id))
        d = deals.one()

        # Contacts
        contacts_count = await db.execute(select(func.count()).where(CrmContact.organization_id == org_id))
        total_contacts = contacts_count.scalar() or 0

        # Leads
        leads = await db.execute(select(
            func.count().label("total"),
            func.count().filter(CrmLead.status == "new").label("new_leads"),
            func.count().filter(CrmLead.status == "qualified").label("qualified"),
            func.count().filter(CrmLead.status == "converted").label("converted"),
        ).where(CrmLead.organization_id == org_id))
        l = leads.one()

        total_closed = d.won_deals + d.lost_deals
        win_rate = round((d.won_deals / total_closed * 100) if total_closed > 0 else 0, 1)

        return {
            "total_contacts": total_contacts,
            "total_deals": d.total_deals,
            "open_deals": d.open_deals,
            "won_deals": d.won_deals,
            "lost_deals": d.lost_deals,
            "pipeline_value": float(d.pipeline_value),
            "won_value": float(d.won_value),
            "win_rate": win_rate,
            "total_leads": l.total,
            "new_leads": l.new_leads,
            "qualified_leads": l.qualified,
            "converted_leads": l.converted,
        }
