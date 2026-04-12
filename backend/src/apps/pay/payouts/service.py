"""Business logic for SavvyPay payouts."""

from __future__ import annotations
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.pay.payouts.models import PayPayout
from src.apps.pay.payouts.schemas import PayoutCreate
from src.apps.pay.wallets.service import WalletService
from src.apps.pay.fees.service import FeeService
from src.apps.pay.ledger.service import LedgerEngine
from src.apps.pay.ledger.schemas import JournalCreate, LedgerEntryLine, AccountCreate


class PayoutService:

    @staticmethod
    async def create_payout(db: AsyncSession, org_id: uuid.UUID, data: PayoutCreate) -> PayPayout:
        wallet = await WalletService.get_wallet(db, org_id, data.wallet_id)
        balance = float(await LedgerEngine.get_balance(db, wallet.available_account_id))
        if balance < data.amount:
            raise ValidationError(f"Insufficient funds: available={balance}")

        fee = await FeeService.calculate_fee(db, org_id, data.amount, "payout")
        net = Decimal(str(data.amount)) - fee

        payout = PayPayout(
            organization_id=org_id, wallet_id=data.wallet_id,
            amount=data.amount, fee=float(fee), net_amount=float(net),
            method=data.method, bank_details=data.bank_details,
            scheduled_date=data.scheduled_date, idempotency_key=data.idempotency_key,
        )
        db.add(payout)
        await db.flush()

        # Debit wallet, credit clearing
        accounts = await LedgerEngine.list_accounts(db, org_id)
        clearing = next((a for a in accounts if a.account_type == "platform_clearing"), None)
        if clearing is None:
            clearing = await LedgerEngine.create_account(db, org_id, AccountCreate(
                code="PLATFORM-CLEARING", name="Platform Clearing", account_type="platform_clearing"))

        lines = [
            LedgerEntryLine(account_id=clearing.id, entry_type="debit", amount=data.amount, description=f"Payout {payout.id}"),
            LedgerEntryLine(account_id=wallet.available_account_id, entry_type="credit", amount=data.amount, description=f"Payout {payout.id}"),
        ]
        if float(fee) > 0:
            fee_account = next((a for a in accounts if a.account_type == "platform_fees"), None)
            if fee_account is None:
                fee_account = await LedgerEngine.create_account(db, org_id, AccountCreate(
                    code="PLATFORM-FEES", name="Platform Fees", account_type="platform_fees"))
            lines.append(LedgerEntryLine(account_id=fee_account.id, entry_type="debit", amount=float(fee), description="Payout fee"))
            lines.append(LedgerEntryLine(account_id=clearing.id, entry_type="credit", amount=float(fee), description="Payout fee"))

        await LedgerEngine.post_journal(db, org_id, JournalCreate(
            lines=lines, source_app="pay",
            idempotency_key=data.idempotency_key or f"payout_{payout.id}",
        ))

        await LedgerEngine.emit_event(db, org_id, "payout.created", "payout", payout.id,
            {"amount": data.amount, "fee": float(fee), "net": float(net)})

        await db.refresh(payout)
        return payout

    @staticmethod
    async def list_payouts(db: AsyncSession, org_id: uuid.UUID) -> list[PayPayout]:
        return list((await db.execute(select(PayPayout).where(PayPayout.organization_id == org_id).order_by(PayPayout.created_at.desc()))).scalars().all())
