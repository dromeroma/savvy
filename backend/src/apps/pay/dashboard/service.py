"""SavvyPay dashboard KPIs."""

from __future__ import annotations
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.pay.transactions.models import PayTransaction
from src.apps.pay.wallets.models import PayWallet
from src.apps.pay.payouts.models import PayPayout


class PayDashboardService:
    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        tx = await db.execute(select(
            func.count().label("total"),
            func.count().filter(PayTransaction.status == "captured").label("captured"),
            func.count().filter(PayTransaction.status == "settled").label("settled"),
            func.coalesce(func.sum(PayTransaction.amount).filter(PayTransaction.status.in_(["captured", "settled"])), 0).label("volume"),
            func.coalesce(func.sum(PayTransaction.fee_amount).filter(PayTransaction.status.in_(["captured", "settled"])), 0).label("fees"),
        ).where(PayTransaction.organization_id == org_id))
        r = tx.one()

        wallets = await db.execute(select(func.count()).where(PayWallet.organization_id == org_id))
        payouts = await db.execute(select(
            func.count().label("total"),
            func.coalesce(func.sum(PayPayout.amount), 0).label("volume"),
        ).where(PayPayout.organization_id == org_id))
        p = payouts.one()

        return {
            "total_transactions": r.total,
            "captured_transactions": r.captured,
            "settled_transactions": r.settled,
            "transaction_volume": float(r.volume),
            "total_fees_collected": float(r.fees),
            "total_wallets": wallets.scalar() or 0,
            "total_payouts": p.total,
            "payout_volume": float(p.volume),
        }
